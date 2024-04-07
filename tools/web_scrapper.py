import re
import threading
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class Scrape:
    def __init__(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode (no browser window)
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.url_to_parse = url
        self.driver.get(url)

    def get_navigation_links(self):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        nav = soup.find('nav').find_all('a')
        parse_url = self.url_to_parse
        if parse_url.endswith('/'):
            parse_url = parse_url.rstrip('/')
        links = []
        for link in nav:
            url = link.get('href')
            text = link.text
            if url:
                # Check if the href is a complete URL
                if re.match(r"^https?://", url):
                    pass
                # Check if the href starts with '//' (protocol-relative URL)
                elif url.startswith('//'):
                    url = f"https:{url}"
                # Check if the href starts with '/'
                elif url.startswith('/'):
                    url = f"{parse_url}{url}"
                # Otherwise, append the base URL
                else:
                    url = f"{parse_url}/{url}"
                links.append((url, text))
        return links

    def get_h1_and_text(self):
        links = self.get_navigation_links()
        h1_texts = []
        for url, text in links:
            self.driver.get(url)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            title = soup.find('title').text
            h1 = soup.find('h1')
            text = f"Information about menu Item: {text}\n"
            text += f"Page Title: {title}"
            if h1:
                text += f"{url}\n"
                text += f"H1: {h1.get_text(strip=True)}\n"
                next_sibling = h1.find_next_sibling(text=True)
                if next_sibling:
                    text += f"Content: - {next_sibling.strip()}\n"
                h1_texts.append(text)
        self.driver.quit()
        return "\n".join(h1_texts)

    def get_navlinks_info(self, url, text):
        self.driver.get(url)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        h1 = soup.find('h1')
        output = f"Page Name: {text}\n\n"
        if h1:
            output += f"H1: {h1.get_text(strip=True)}\n"
            h_p = h1.find_next('p')
            if h_p:
                output += f"P: {h_p.get_text(strip=True)}\n"
            h2 = soup.find('h2')
            if h2:
                output += f"H2: {h2.get_text(strip=True)}\n"
                p = h2.find_next('p')
                if p:
                    output += f"P: {p.get_text(strip=True)}\n"
        return output

    def count_custom_tags(self, urls):
        results = {}  # Dictionary to store results for each URL
        tags = ['button', 'img', 'section']
        class_names = ["hero", "slider"]
        for url in urls:
            self.driver.get(url)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            output = []
            tag_counts = {}
            classes_counts = {}
            output.append(f"\nComments:\n")
            for tag in tags:
                elements = soup.find_all(tag)
                tag_counts[tag] = len(elements)
                if len(elements) > 15:
                    output.append(f"A lot of <{tag}> found: ({len(elements)})")
                else:
                    output.append(f"Found total {len(elements)} <{tag}> elements")

            for class_name in class_names:
                our_classes = [element for element in soup.find_all(class_=True) if
                               any(class_name in class_ for class_ in element['class'])]
                classes_counts[class_name] = len(our_classes)
                if len(our_classes) > 0:
                    output.append(f"Found {len(our_classes)} elements containing '{class_name}'")
                else:
                    output.append(f"Found no elements containing '{class_name}'")

            results = "\n".join(output)

        return results

    def find_potential_cta_texts(self, urls):
        # Dictionary to store results for each URL
        for url in urls:
            self.driver.get(url)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            potential_cta_texts = set()
            potential_cta_texts.add("Potential CTAS: \n")
            # Define keywords and phrases that are commonly used in CTAs
            cta_keywords = ['buy', 'sign up', 'learn more', 'subscribe', 'register', 'start', 'join', 'get started',
                            'shop', 'order', 'download', 'try']
            # Check both buttons and links (a tags)
            for element in soup.find_all(['button', 'a']):
                text = element.get_text().lower().strip().title()
                class_id = " ".join(element.get('class', []) + [element.get('id', '')]).lower()
                href = element.get('href', '').lower()
                # Check if the text, class, or ID contains any CTA keywords
                if any(keyword in text for keyword in cta_keywords) or any(
                    keyword in class_id for keyword in cta_keywords):
                    potential_cta_texts.add(text)
                # Check if the link leads to a typical CTA destination
                elif any(keyword in href for keyword in ['signup', 'register', 'order', 'download']):
                    potential_cta_texts.add(text)
            return '\n'.join(potential_cta_texts)

    def get_n_hierarchy(self):
        response = requests.get(self.url_to_parse)

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        for x in soup.find_all(['header', 'nav', 'form', 'head', 'script', 'noscript', 'style', 'link', 'footer']):
            x.extract()
        # Find all the h tags, p tags, and a tags in the page
        tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'span'])

        # Function to check if a tag is a heading tag
        def is_heading_tag(tag):
            return tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        # Function to get the <a> tag with text or image alt text
        def get_a_tag(a_tag):
            link_text = a_tag.get_text(strip=True)
            if not link_text:
                img_tag = a_tag.find('img', alt=True)
                if img_tag:
                    link_text = f"image alt text: {img_tag['alt']}"
            if link_text and a_tag.has_attr('href'):
                return f"{link_text} (link: {a_tag['href']})"
            elif link_text:
                return link_text
            return None

        # Iterate through the tags and collect the content
        output = {}
        section_count = 0
        current_section = None
        for tag in tags:
            if is_heading_tag(tag):
                # Start a new section for each heading tag
                section_count += 1
                section_key = f"Section {section_count}"
                current_section = {tag.name: tag.get_text(strip=True)}
                output[section_key] = current_section
            elif tag.name == 'a' and current_section is not None:
                # Add <a> tags to the current section
                a_output = get_a_tag(tag)
                if a_output:
                    if "a" not in current_section:
                        current_section["a"] = []
                    current_section["a"].append(a_output)
            elif tag.name == 'p' and current_section is not None:
                # Add <p> tags to the current section
                if "p" not in current_section:
                    current_section["p"] = []
                current_section["p"].append(tag.get_text(strip=True))

        return output

    def get_navigation_menu(self, include_submenus=False):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        nav = soup.find('nav')  # Find the navigation menu
        if nav:
            return self.get_menu_items(nav, include_submenus=include_submenus)
        return []

    def get_main_menu_links(self):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        nav = soup.find('nav')
        if nav is None:
            print("Nav element not found")
            return []

        main_menu_items = ""

        # Check if a tag is not nested within another a tag
        for a_tag in nav.find_all('ul'):
            for li in a_tag.find_next('li'):
                main_menu_items += f"asd - {li.get_text()}"

        if not main_menu_items:
            print("No main menu items found")

        return '\n'.join(main_menu_items)

    def close(self):
        self.driver.quit()
