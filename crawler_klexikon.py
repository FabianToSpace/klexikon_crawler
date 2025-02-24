# crawler_klexikon.py
import pandas as pd
from tqdm import tqdm

from crawler import (
    get_soup,
    remove_divs_by_class,
    remove_after_div_class,
    extract_paragraphs,
    split_into_sentences
)

def crawl_klexikon(start_url="https://klexikon.zum.de/wiki/Kategorie:Klexikon-Artikel", max_pages=None):
    """
    Crawl Klexikon articles starting at 'start_url'.
    1) Paginate over 'nächste Seite' links to gather article URLs.
    2) For each article, remove 'klexibox' divs and truncate at 'mw-inputbox-centered'.
    3) Extract paragraphs and split them into sentences.
    Returns a DataFrame: ID | WikiLink | Paragraphs | Sentences
    """
    base_url = "https://klexikon.zum.de"
    all_article_urls = []
    current_url = start_url
    page_count = 0
    
    # Collect article URLs from paginated category pages
    while True:
        soup = get_soup(current_url)
        links = soup.select("div.mw-category a")
        for link in links:
            href = link.get("href")
            if href and href.startswith("/wiki/"):
                full_url = base_url + href
                all_article_urls.append(full_url)
        
        # Find "nächste Seite" link
        next_link = soup.find("a", string="nächste Seite")
        if not next_link:
            break
        
        current_url = base_url + next_link["href"]
        page_count += 1
        
        if max_pages and page_count >= max_pages:
            break
    
    # Build the dataset
    data_records = []
    for idx, article_url in enumerate(tqdm(all_article_urls, desc="Klexikon Articles"), start=1):
        soup = get_soup(article_url)
        
        # Remove site-specific unwanted content
        remove_divs_by_class(soup, "klexibox")
        remove_after_div_class(soup, "mw-inputbox-centered")
        
        # Extract paragraphs
        paragraphs = extract_paragraphs(soup)
        
        # Split paragraphs into sentences
        all_sentences = []
        for para in paragraphs:
            all_sentences.extend(split_into_sentences(para))
        
        data_records.append({
            "ID": idx,
            "WikiLink": article_url,
            "Paragraphs": paragraphs,
            "Sentences": all_sentences
        })
    
    df = pd.DataFrame(data_records, columns=["ID", "WikiLink", "Paragraphs", "Sentences"])
    return df
