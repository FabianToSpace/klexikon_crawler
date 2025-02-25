# crawler_miniklexikon.py
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import requests

from crawler import get_soup, remove_divs_by_class, remove_after_hr, extract_content, split_into_sentences

def _fetch_article(url, session):
    """
    Fetch a single MiniKlexikon article using the shared functions.
    It removes unwanted elements (like "klexibox") and then truncates the content at the first <hr> tag.
    It extracts paragraphs and splits them into sentences.
    """
    try:
        soup = get_soup(url, session)
        remove_divs_by_class(soup, "klexibox")
        remove_after_hr(soup)
        paragraphs = extract_content(soup)
        sentences = []
        for para in paragraphs:
            sentences.extend(split_into_sentences(para))
        return {"WikiLink": url, "Paragraphs": paragraphs, "Sentences": sentences}
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return {"WikiLink": url, "Paragraphs": [], "Sentences": []}

def crawl_miniklexikon(start_url="https://miniklexikon.zum.de/wiki/Kategorie:Alle_Artikel", max_pages=None, max_workers=2):
    """
    Crawl MiniKlexikon articles:
      - Collect article URLs from category pages (using "nächste Seite" pagination)
      - Use ThreadPoolExecutor to fetch articles concurrently
      - Process each article with the shared core logic
    Returns a Pandas DataFrame with columns: ID, WikiLink, Paragraphs, Sentences.
    """
    base_url = "https://miniklexikon.zum.de"
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
