
# Company Website Analysis Tool

## Overview

   This tool is designed to analyze company websites, scrape relevant data, and generate comprehensive reports in Excel format. 
   It uses BeautifulSoup for web scraping, OpenPyXL for Excel file manipulation, and dotenv for environment variable management.

## Features

   - Scrapes navigation links and page hierarchy from the company's homepage.
   - Analyzes the homepage and other pages to generate descriptions and insights.
   - Identifies target audiences based on the content.
   - Extracts potential Call-To-Actions (CTAs) from the pages.
   - Generates an Excel report with detailed analysis of the website.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repository.git
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Set your OpenAI API key in the `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
2. Run the tool:
   ```bash
   python main.py
   ```
3. Follow the prompts to enter the company name and website URL.
4. The tool will scrape the data, analyze it, and generate a report in the `companies` folder.

## License

This project is licensed under the [MIT License](LICENSE).