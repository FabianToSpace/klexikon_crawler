# crawler_wikijunior.py
import requests
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from crawler import get_soup

def extract_wikijunior_content(url, session=None):
    """
    Fetch and parse a Wikijunior chapter content page.
    - Locate the div with id "mw-content-text"
    - Remove any <table> elements within it
    - Recursively extract all <p> and header tags (h1–h6) in document order.
    Returns a list of text paragraphs.
    """
    soup = get_soup(url, session)
    if not soup:
        return []
    content_div = soup.find("div", id="mw-content-text")
    if not content_div:
        return []
    for table in content_div.find_all("table"):
        table.decompose()
    elements = content_div.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])
    paragraphs = []
    for element in elements:
        text = element.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)
    return paragraphs

def parse_links(list_element, base_url, parent_href=None):
    """
    Parse an <ol> or <ul> element containing chapter or subchapter links.
    If a parent_href is provided, skip links that are duplicates (i.e. only differ by an anchor).
    Also, if an <li> contains multiple <a> tags, select the first one that does not contain an <img>.
    Returns a list of dictionaries with keys: "text", "href", "title", and (optionally) "subchapters".
    """
    links = []
    for li in list_element.find_all("li", recursive=False):
        a_tags = li.find_all("a")
        selected_a = None
        for a in a_tags:
            if a.find("img"):
                continue
            selected_a = a
            break
        if not selected_a:
            continue
        raw_href = selected_a.get("href")
        link_url = requests.compat.urljoin(base_url, raw_href)
        if parent_href is not None:
            if link_url.split('#')[0] == parent_href.split('#')[0]:
                continue
        link_info = {
            "text": selected_a.get_text(strip=True),
            "href": link_url,
            "title": selected_a.get("title")
        }
        nested_list = li.find(["ol", "ul"])
        if nested_list:
            subchapters = parse_links(nested_list, base_url, parent_href=link_url)
            if subchapters:
                link_info["subchapters"] = subchapters
        links.append(link_info)
    return links

def crawl_wikijunior_toc(toc_url, session=None):
    """
    Parse a Wikijunior Table-of-Contents (TOC) page.
    - Finds the main container with id "mw-content-text"
    - Iterates over chapter header divs (class "mw-heading"), extracts the chapter title,
      and retrieves the next sibling list (ol or ul) containing the links.
    - Skips chapters titled "Zusammenfassung des Projekts".
    Returns a list of chapters (each a dict with "chapter" and "links").
    """
    soup = get_soup(toc_url, session)
    if not soup:
        return []
    toc_div = soup.find("div", id="mw-content-text")
    if not toc_div:
        return []
    chapters = []
    for header_div in toc_div.find_all("div", class_="mw-heading"):
        heading_tag = header_div.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not heading_tag:
            continue
        chapter_title = heading_tag.get_text(" ", strip=True)
        if chapter_title == "Zusammenfassung des Projekts":
            continue
        list_tag = header_div.find_next_sibling(["ol", "ul"])
        if not list_tag:
            continue
        chapter_links = parse_links(list_tag, toc_url)
        chapters.append({
            "chapter": chapter_title,
            "links": chapter_links
        })
    return chapters

def crawl_wikijunior_toc_and_content(toc_url, max_workers=4):
    """
    Crawl a Wikijunior TOC page, then for each chapter link, fetch its content page.
    Extract the book title from the TOC page’s <title> element.
    Returns a DataFrame with columns:
      BookTitle, Chapter, LinkText, WikiLink, Paragraphs.
    """
    session = requests.Session()
    toc_soup = get_soup(toc_url, session)
    book_title = "Unknown"
    if toc_soup:
        title_tag = toc_soup.find("title")
        if title_tag:
            book_title = title_tag.get_text(" ", strip=True)
    toc_structure = crawl_wikijunior_toc(toc_url, session)
    results = []
    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for chapter in toc_structure:
            chapter_title = chapter["chapter"]
            for link in chapter["links"]:
                future = executor.submit(extract_wikijunior_content, link["href"], session)
                tasks.append((future, chapter_title, link["text"], link["href"]))
                if "subchapters" in link:
                    for sub_link in link["subchapters"]:
                        future = executor.submit(extract_wikijunior_content, sub_link["href"], session)
                        tasks.append((future, chapter_title, sub_link["text"], sub_link["href"]))
        for future, chapter_title, link_text, url in tasks:
            paragraphs = future.result()
            results.append({
                "BookTitle": book_title,
                "Chapter": chapter_title,
                "LinkText": link_text,
                "WikiLink": url,
                "Paragraphs": paragraphs
            })
    df = pd.DataFrame(results, columns=["BookTitle", "Chapter", "LinkText", "WikiLink", "Paragraphs"])
    return df

# --- Print Version Parsing ---
def crawl_wikijunior_print(url, session=None):
    """
    Parse a Wikijunior print version page where all content is on a single page.
    The page is assumed to be divided into sections by headlines (h1–h6) with following paragraphs.
    Returns a DataFrame with columns:
      BookTitle, Chapter, LinkText, WikiLink, Paragraphs.
    """
    if session is None:
        session = requests.Session()
    soup = get_soup(url, session)
    if not soup:
        return pd.DataFrame(columns=["BookTitle", "Chapter", "LinkText", "WikiLink", "Paragraphs"])
    title_tag = soup.find("title")
    book_title = title_tag.get_text(" ", strip=True) if title_tag else "Unknown"
    content_div = soup.find("div", id="mw-content-text")
    if not content_div:
        return pd.DataFrame(columns=["BookTitle", "Chapter", "LinkText", "WikiLink", "Paragraphs"])
    elements = content_div.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"], recursive=True)
    sections = []
    current_section = None
    for el in elements:
        if el.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            if current_section is not None:
                sections.append(current_section)
            current_section = {"headline": el.get_text(" ", strip=True), "paragraphs": []}
        elif el.name == "p":
            if current_section is None:
                current_section = {"headline": "Introduction", "paragraphs": []}
            text = el.get_text(" ", strip=True)
            if text:
                current_section["paragraphs"].append(text)
    if current_section is not None:
        sections.append(current_section)
    results = []
    for section in sections:
        results.append({
            "BookTitle": book_title,
            "Chapter": section["headline"],
            "LinkText": section["headline"],
            "WikiLink": url,
            "Paragraphs": section["paragraphs"]
        })
    df = pd.DataFrame(results, columns=["BookTitle", "Chapter", "LinkText", "WikiLink", "Paragraphs"])
    return df

def crawl_wikijunior():
    """
    Main function to crawl Wikijunior pages.
    A pre-configured list of URLs (each with a type: "toc" or "print") is used.
    The results from all pages are concatenated into one DataFrame.
    """
    pages = [
        {"url": "https://de.wikibooks.org/wiki/Wikijunior_Computer_und_Internet", "type": "toc"},
        {"url": "https://de.wikibooks.org/wiki/Wikijunior_Sonnensystem/_Druckversion", "type": "print"},
        {"url": "https://de.wikibooks.org/wiki/Wikijunior_Die_Elemente/_Druckversion", "type": "print"},
        {"url": "https://de.wikibooks.org/wiki/Wikijunior_Entwicklung_des_Lebens/_Druckversion", "type": "print"},
        {"url": "https://de.wikibooks.org/wiki/Wikijunior_Sprachen/_Druckversion", "type": "print"},
        {"url": "https://de.wikibooks.org/wiki/Wikijunior_Europa/_Druckversion", "type": "print"},
        {"url": "https://de.wikibooks.org/wiki/Wikijunior_Gro%C3%9Fkatzen/_Druckversion", "type": "print"},
        {"url": "https://de.wikibooks.org/wiki/Wikijunior_Die_Elemente/_Druckversion", "type": "print"}
    ]
    dfs = []
    session = requests.Session()
    for page in pages:
        url = page["url"]
        page_type = page["type"]
        if page_type == "toc":
            df = crawl_wikijunior_toc_and_content(url, max_workers=4)
        elif page_type == "print":
            df = crawl_wikijunior_print(url, session)
        else:
            continue
        dfs.append(df)
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
    else:
        combined_df = pd.DataFrame(columns=["BookTitle", "Chapter", "LinkText", "WikiLink", "Paragraphs"])
    return combined_df
