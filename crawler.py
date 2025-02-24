# crawler.py
import requests
from bs4 import BeautifulSoup
import re

def get_soup(url):
    """
    Fetch and parse a URL, returning a BeautifulSoup object.
    Raises an exception on request errors.
    """
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

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
        # Remove siblings after target_div
        sibling = target_div.next_sibling
        while sibling:
            next_sibling = sibling.next_sibling
            sibling.decompose()
            sibling = next_sibling
        # Finally remove target_div itself
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

def extract_paragraphs(soup):
    """
    From the main content area (div.mw-parser-output), return a list of paragraph texts.
    """
    paragraphs = []
    content_div = soup.find("div", class_="mw-parser-output")
    if not content_div:
        return paragraphs
    
    for p in content_div.find_all("p"):
        p_text = p.get_text(" ", strip=True)
        if p_text:
            paragraphs.append(p_text)
    
    return paragraphs

def split_into_sentences(paragraph):
    """
    Naive splitting of a paragraph into sentences by '.', '?', or '!' + whitespace/end.
    Returns a list of sentence strings.
    """
    sentences = re.split(r'[.?!]+(?:\s+|$)', paragraph)
    # Remove empty strings and strip whitespace
    return [s.strip() for s in sentences if s.strip()]
