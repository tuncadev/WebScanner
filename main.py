import os
import time
from datetime import datetime
from os.path import exists
from tools.colors import ChangeColor
from openpyxl import Workbook
from dotenv import load_dotenv
from openpyxl.reader.excel import load_workbook
from crewai import Agent, Task, Crew, Process
from textwrap import dedent
from langchain_openai import ChatOpenAI
from tools.web_scrapper import Scrape


def url_exists(url):
    # For debug purposes -> print("Starting url_exists function...")
    import requests
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Something went wrong: {e}")
        return False


def validate_url(prompt):
    # For debug purposes -> print("Starting validate_url function...")
    import re
    import validators
    while True:
        url = input(prompt)
        if not re.match(r"https?://", url):
            url = f"https://{url}"
        if not url.endswith('/'):
            url += '/'
        if validators.url(url) and url_exists(url):
            return url
        else:
            print(change_color.make_red("Please input a valid URL or make sure the URL exists."))


# Start time and date
def gather_info():
    # Prompt user for company information
    print(change_color.make_yellow("Please provide some information about the company we will analyze:"))
    company_name = input(change_color.make_yellow(f"Please enter company name: "))
    company_website = validate_url(
        change_color.make_yellow(f"Please enter the homepage of {company_name} (https://www.example.com/): "))
    print(change_color.make_green(f"Thank you! Creating necessary files and folders..."))
    if create_file(company_name):
        start_analysis(company_name, company_website)


def create_file(company_name):
    try:
        # Set up report folder and file paths
        report_folder_path = f"companies/{company_name}"
        folder_exists = os.path.exists(report_folder_path)

        # Load or create the Excel workbook for the report
        if not folder_exists:
            os.makedirs(report_folder_path)
        print(change_color.make_yellow("All Done! Folders and Files ready!"))
        return True
    except:
        print("Something went wrong while creating the necessary files. Please Debug")
        return False


def start_analysis(company_name, company_website):
    print(change_color.make_green(f"We are starting the analysis.,,"))
    report_folder_path = f"companies/{company_name}"
    # Load environment variables
    load_dotenv()
    openai_api = os.getenv("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = str(openai_api)
    started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(change_color.make_yellow(f"Started at: {started_at}"))
    time.sleep(3)

    # Initialize the web scraper
    print(change_color.make_green(f"Scraping data from website...Be patient please, get a cup of coffee..."))
    scraper = Scrape(company_website)
    navigation_links = scraper.get_navigation_links()
    number_of_pages = len(navigation_links)
    homepage_data = scraper.get_n_hierarchy()
    menu_items = scraper.get_navigation_links()

    # Initialize CrewAI agents for analysis
    homepage_analyzer = Agent(
        role="Company analyzer",
        goal="Analyze the given brief website information from company's homepage, write a one paragraph website "
             "description",
        backstory="You are an experienced website analyzer. You receive a brief information about a company's "
                  "website, and analyze their content nad write a description about the site",
        allow_delegation=False,
        verbose=False,
        llm=ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3
        )
    )
    page_analyzer = Agent(
        role="Company analyzer",
        goal="Analyze the given brief page information from one of the company's pages, write a one paragraph "
             "page description. What is the page about.",
        backstory="You are an experienced web page analyzer. You receive a brief information about a company's "
                  "web page, and analyze their content nad write a description about the page. You recieve "
                  "information such as h tags, some text, some information about certain tags,  classes, "
                  "and information about possible CATs",
        allow_delegation=False,
        verbose=False,
        llm=ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3
        )
    )

    # Create and execute tasks for homepage and audience analysis
    website_analysis_task = Task(
        description=dedent(f"Analyze the information below in JSON format, and write a one paragraph conclusion "
                           f"about the company"
                           f"website. \nContent:\n\n{homepage_data}"),
        expected_output=f"A brief information about the given webpage, analyzing the content given in the "
                        f"description",
        agent=homepage_analyzer,
    )

    audience_analysis_task = Task(
        description=dedent(
            f"Analyze the information below in JSON format, and write a one paragraph conclusion about the company's "
            f"target audience'."
            f"\nContent:\n\n{homepage_data}"),
        expected_output=f"A brief information about company's target audience, analyzing the content given in the "
                        f"description",
        agent=homepage_analyzer,
    )
    audience_task = audience_analysis_task.execute()
    homepage_task = website_analysis_task.execute()
    print(change_color.make_green(f"Almost there..."))

    # Load and Fill in the Excel report with analysis results
    empty_file_path = f'companies/empty-report.xlsx'
    # Worksheet Company Details
    wb = load_workbook(empty_file_path)
    ws1 = wb.worksheets[0]
    ws1['B2'] = f"{company_name}"
    ws1['B3'] = f"{company_website}"
    ws1['B4'] = f"{homepage_task}"
    ws1['B6'] = f"{number_of_pages} (Based on the analysis of the menu items. Actual number of pages might vary)"
    ws1['B7'] = f"{audience_task}"

    # Worksheet Analysis report
    ws2 = wb.worksheets[1]
    print(f"Number of pages to be analyzed: {number_of_pages}")
    i = 1
    row = 2
    print(change_color.make_yellow("Let's start the journey!!!"))
    completed = False
    # For every page in gathered menu items gather information and write to workbook analysis sheet
    for url, text in navigation_links:
        comments_row = ""
        print(f"Pages left {number_of_pages - i}")
        if url.endswith('#'):
            url = url.rstrip('#')
        scraper.driver.get(url)  # Navigate to the URL
        comments = scraper.count_custom_tags([url])  # Get comments (custom tags count)
        nav_info = scraper.get_navlinks_info(url, text)
        comments_row += f"{nav_info}"
        comments_row += f"{comments}"

        ctas = scraper.find_potential_cta_texts([url])  # Get CTAs
        # Run the page analyzer task
        page_analysis_task = Task(
            description=dedent(
                f"Analyze the webpage titled: {text}, and write a one paragraph general conclusion about the given page content'. "
                f"\nContent:\n\n{comments_row}"),
            expected_output=f"The analysis of the page {text} with  the given webpage information, analyzing"
                            f"the content given in the description and write your conclusions",
            agent=page_analyzer,
        )
        conclusion = page_analysis_task.execute()
        if conclusion:
            # Write results to worksheet
            ws2[f'A{row}'] = f"{text}"
            ws2[f'B{row}'] = f"{url}"
            ws2[f'C{row}'] = f"{comments_row}"
            ws2[f'D{row}'] = f"{ctas}"
            ws2[f'E{row}'] = f"{conclusion}"
            i = i + 1
            row = row + 1
            completed = True
    if completed:
        wb.save(f"{report_folder_path}/{company_name}-report.xlsx")
        ended_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(change_color.make_green("All done!"))
        print(change_color.make_yellow(f"Finished at: {ended_at}"))
        scraper.close()


def main():
    gather_info()


if __name__ == "__main__":
    # Initialize color changer for console messages
    change_color = ChangeColor()
    main()
