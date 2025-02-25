# crawler_klexikon.py
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import requests

from crawler import get_soup, remove_divs_by_class, remove_after_div_class, extract_content, split_into_sentences

def _fetch_article(url, session):
    """
    Fetch a single article using the core functions from crawler.py.
    This function removes unwanted elements (like "klexibox" and the "mw-inputbox-centered" marker)
    and extracts paragraphs and sentences.
    """
    try:
        soup = get_soup(url, session)
        remove_divs_by_class(soup, "klexibox")
        remove_after_div_class(soup, "mw-inputbox-centered")
        paragraphs = extract_content(soup)
        sentences = []
        for para in paragraphs:
            sentences.extend(split_into_sentences(para))
        return {"WikiLink": url, "Paragraphs": paragraphs, "Sentences": sentences}
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return {"WikiLink": url, "Content": [], "Sentences": []}


def crawl_klexikon(start_url="https://klexikon.zum.de/wiki/Kategorie:Klexikon-Artikel", max_pages=None, max_workers=2):
    """
    Crawl Klexikon articles:
      - Gather article URLs from the category pages (following "nächste Seite" links)
      - Use a ThreadPoolExecutor to fetch articles concurrently (speeding up the crawl)
      - Extract content using the core logic defined in crawler.py
    Returns a Pandas DataFrame with columns: ID, WikiLink, Paragraphs, Sentences.
    """
    base_url = "https://klexikon.zum.de"
    all_article_urls = []
    current_url = start_url
    page_count = 0

    while True:
        soup = get_soup(current_url)
        links = soup.select("div.mw-category a")
        for link in links:
            href = link.get("href")
            if href and href.startswith("/wiki/"):
                full_url = base_url + href
                all_article_urls.append(full_url)
        next_link = soup.find("a", string="nächste Seite")
        if not next_link:
            break
        current_url = base_url + next_link["href"]
        page_count += 1
        if max_pages and page_count >= max_pages:
            break

    data_records = []
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_fetch_article, url, session): url for url in all_article_urls}
            for idx, future in enumerate(tqdm(as_completed(futures), total=len(futures), desc="Processing Articles"), start=1):
                result = future.result()
                result["ID"] = idx
                data_records.append(result)

    df = pd.DataFrame(data_records, columns=["ID", "WikiLink", "Paragraphs", "Sentences"])
    return df
