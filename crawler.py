# crawler.py
import requests
from bs4 import BeautifulSoup
import re

def get_soup(url, session=None):
    """
    Fetch and parse a URL, returning a BeautifulSoup object.
    If a requests.Session is provided, use it; otherwise, fallback to requests.get.
    If any error occurs, log the error and return None.
    """
    try:
        if session:
            response = session.get(url)
        else:
            response = requests.get(url)
        response.raise_for_status()
        if "projekt-gutenberg.org" in url:
            response.encoding = "utf-8"  # Force UTF-8 encoding for Projekt Gutenberg pages.
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def remove_divs_by_class(soup, class_name):
    """
    Remove all <div> elements that have a given CSS class.
    """
    for div in soup.find_all("div", class_=class_name):
        div.decompose()

def remove_after_div_class(soup, class_name):
    """
    Find the first <div> of a given class and remove it plus all siblings after it.
    Useful for truncating at that div.
    """
    target_div = soup.find("div", class_=class_name)
    if target_div:
        sibling = target_div.next_sibling
        while sibling:
            next_sibling = sibling.next_sibling
            sibling.decompose()
            sibling = next_sibling
        target_div.decompose()

def remove_after_hr(soup):
    """
    Find the first <hr> element and remove it plus all siblings after it.
    Useful if the site uses an <hr> to indicate the end of main content.
    """
    hr_tag = soup.find("hr")
    if hr_tag:
        sibling = hr_tag.next_sibling
        while sibling:
            next_sibling = sibling.next_sibling
            sibling.decompose()
            sibling = next_sibling
        hr_tag.decompose()

def extract_content(soup, stop_marker="mw-inputbox-centered"):
    """
    From the main content area (div.mw-parser-output), extract text from paragraphs and headings (h1-h6)
    in the order they appear, stopping when a tag with class stop_marker is encountered.
    Returns a list of text strings.
    """
    content = []
    parser_div = None
    for div in soup.find_all("div", class_="mw-parser-output"):
        if div.find_parent("div", id="mw-content-text"):
            parser_div = div
            break
    if not parser_div:
        parser_div = soup.find("div", class_="mw-parser-output")
    if not parser_div:
        return content

    for element in parser_div.contents:
        if hasattr(element, "name"):
            if element.name == "div" and stop_marker in element.get("class", []):
                break
            if element.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6"]:
                text = element.get_text(" ", strip=True)
                if text:
                    content.append(text)
    return content


def split_into_sentences(paragraph):
    """
    Naive splitting of a paragraph into sentences by '.', '?', or '!' + whitespace/end.
    Returns a list of sentence strings.
    """
    sentences = re.split(r'[.?!]+(?:\s+|$)', paragraph)
    return [s.strip() for s in sentences if s.strip()]
