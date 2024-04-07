import os
from os.path import exists
from tools.colors import ChangeColor
from openpyxl import Workbook
from dotenv import load_dotenv
from openpyxl.reader.excel import load_workbook
from crewai import Agent, Task, Crew, Process
from textwrap import dedent
from langchain_openai import ChatOpenAI
from tools.web_scrapper import Scrape

load_dotenv()
openai_api = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = str(openai_api)

change_color = ChangeColor()

print(change_color.make_yellow("Please provide some information about the company we will analyze:"))
company_name = input(change_color.make_yellow(f"Please enter company name: "))
company_website = input(change_color.make_yellow(f"Please enter the homepage of {company_name} (https://www.example.com/): "))
print(change_color.make_green(f"Thank you! Creating necessary files and folders..."))
report_folder_path = f"companies/{company_name}"
folder_exists = os.path.exists(report_folder_path)
empty_file_path = f'companies/empty-report.xlsx'
wb = load_workbook(empty_file_path)
if not folder_exists:
    os.makedirs(report_folder_path)

print(change_color.make_yellow("All Done! Folders and Files ready!"))
print(change_color.make_green(f"We are starting the analysis.,,"))



scraper = Scrape(company_website)
navigation_links = scraper.get_navigation_links()
number_of_pages = len(navigation_links)
homepage_data = scraper.get_n_hierarchy()
menu_items = scraper.get_navigation_links()
menu_structure = (f"Below is the menu items in order. Please not that menu structure is very difficult to determine by "
                  f"scraping only.\n")
menu_structure += f"Please check the actual website for better understanding the structure.\n\n"
for url, text in menu_items:
    if text and text[0].isalpha():
        menu_structure += f"{text.strip()}"
    else:
        menu_structure +=f" {text.strip()}"
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


ws1 = wb.worksheets[0]
ws1['B2'] = f"{company_name}"
ws1['B3'] = f"{company_website}"
ws1['B4'] = f"{homepage_task}"
ws1['B6'] = f"{number_of_pages} (Based on the analysis of the menu items. Actual number of pages might vary)"
ws1['B7'] = f"{audience_task}"
ws1['B8'] = f"{menu_structure}"
ws2 = wb.worksheets[1]
print(change_color.make_green(f"Scraping data from website...Be patient please, get a cup of coffee..."))
print(f"Number of pages to be analyzed: {number_of_pages}")
i = 1
row = 2
print(f"Let's start!!!")

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
    page_analysis_task = Task(
        description=dedent(
            f"Analyze the webpage titled: {text}, and write a one paragraph general conclusion about the given page'. "
            f"\nContent:\n\n{comments_row}"),
        expected_output=f"The analysis of the page {text} with  the given webpage information, analyzing"
                        f"the content given in the description and write your conclusions",
        agent=page_analyzer,
    )
    conclusion = page_analysis_task.execute()
    ws2[f'A{row}'] = f"{text}"
    ws2[f'B{row}'] = f"{url}"
    ws2[f'C{row}'] = f"{comments_row}"
    ws2[f'D{row}'] = f"{ctas}"
    ws2[f'E{row}'] = f"{conclusion}"
    i = i + 1
    row = row + 1

wb.save(f"{report_folder_path}/{company_name}-report.xlsx")
scraper.close()