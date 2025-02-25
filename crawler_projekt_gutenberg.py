import pandas as pd
import requests
from tqdm import tqdm
import urllib.parse
from crawler import get_soup, split_into_sentences

def is_descendant_of_dropdown(tag):
    """
    Return True if the given tag is inside an element with class "dropdown".
    """
    parent = tag.parent
    while parent:
        if parent.has_attr("class") and "dropdown" in parent.get("class", []):
            return True
        parent = parent.parent
    return False


def crawl_lesetips(start_url="https://www.projekt-gutenberg.org/info/texte/lesetips.html"):
    """
    Crawl the Projekt Gutenberg Lesetips page and extract book links for target categories.
    Only the categories with IDs "ab-12Jahren" and "bis-11-Jahre" are processed.
    
    Returns a list of dictionaries with keys:
      CategoryID, CategoryTitle, BookLink, BookTitle
    """
    base_url = "https://www.projekt-gutenberg.org"
    session = requests.Session()
    soup = get_soup(start_url, session=session)
    target_ids = {"ab-12Jahren", "bis-11-Jahre"}
    records = []
    
    for h4 in soup.find_all("h4"):
        a_tag = h4.find("a", id=True)
        if not a_tag:
            continue
        category_id = a_tag["id"]
        if category_id not in target_ids:
            continue
        category_title = h4.get_text(strip=True)
        # Iterate over siblings until the next h4 is encountered.
        for sibling in h4.find_next_siblings():
            if sibling.name == "h4":
                break
            if sibling.name == "dl":
                for dd in sibling.find_all("dd"):
                    link_tag = dd.find("a")
                    if not link_tag:
                        continue
                    book_link = link_tag.get("href")
                    if book_link:
                        if book_link.startswith("/"):
                            book_link = base_url + book_link
                        elif book_link.startswith(".."):
                            book_link = start_url[:start_url.rfind('/')] + "/" + book_link
                    book_title = link_tag.get_text(strip=True)
                    records.append({
                        "CategoryID": category_id,
                        "CategoryTitle": category_title,
                        "BookLink": book_link,
                        "BookTitle": book_title
                    })
    return records

def fetch_book_content(book_link, session):
    """
    For a given book link on Projekt Gutenberg, fetch the complete text content.
    The content is paginated via a link with text containing "weiter" (>>).
    On each page:
      - Remove any <div> with class "anzeige-chap".
      - Extract text from between the first two <hr> tags using only heading (h1–h6) and paragraph (<p>) tags.
    Returns the combined text content from all pages.
    """
    content_blocks = []
    current_url = book_link
    
    while True:
        soup = get_soup(current_url, session=session)

        if soup is None:
            break
        
        # Remove unwanted elements.
        for div in soup.find_all("div", class_="anzeige-chap"):
            div.decompose()
        
        hrs = soup.find_all("hr")
        page_text = ""
        if len(hrs) >= 2:
            # Extract text between the first and second <hr> tags.
            for element in hrs[0].next_siblings:
                if hasattr(element, "name") and element.name == "hr":
                    break
                if hasattr(element, "name") and element.name in ["h1", "h2", "h3", "h4", "h5", "h6", "p"]:
                    text = element.get_text(" ", strip=True)
                    if text:
                        page_text += text + " "
        else:
            page_text = soup.get_text(" ", strip=True)
        content_blocks.append(page_text.strip())
        
        # Look for the pagination link ("weiter >>")
        candidate_links = soup.find_all("a", string=lambda t: t and "weiter" in t.lower())
        next_link_tag = None
        for link in candidate_links:
            # If the link is not inside a dropdown, select it.
            if not is_descendant_of_dropdown(link):
                next_link_tag = link
                break

        if next_link_tag and next_link_tag.get("href"):
            relative_url = next_link_tag.get("href")
            # Use the current URL as base to resolve the relative link.
            next_url = urllib.parse.urljoin(current_url, relative_url)
            # Prevent an infinite loop if next_url equals current_url.
            if next_url == current_url:
                print(f"Next URL is identical to current URL ({current_url}). Breaking out to avoid loop.")
                break
            current_url = next_url
        else:
            break
    
    full_text = " ".join(content_blocks).strip()
    return full_text


def crawl_projekt_gutenberg(start_url="https://www.projekt-gutenberg.org/info/texte/lesetips.html"):
    """
    Extended crawler for Projekt Gutenberg:
      1. Crawl the Lesetips page to extract book links for target categories 
         ("ab-12Jahren" and "bis-11-Jahre").
      2. For each book link, follow pagination (via the "weiter >>" link) to fetch complete content.
      3. On each page, extract text between the first two <hr> tags, considering only headings and paragraphs.
      4. Split the complete text into sentences.
    
    Returns a Pandas DataFrame with the columns:
      ID, CategoryID, BookLink, BookTitle, Sentences
    """
    books = crawl_lesetips(start_url)
    records = []
    session = requests.Session()
    
    for idx, book in enumerate(tqdm(books, desc="Processing Books"), start=1):
        book_link = book["BookLink"]
        category_id = book["CategoryID"]
        book_title = book["BookTitle"]
        
        full_text = fetch_book_content(book_link, session)
        sentences = split_into_sentences(full_text)
        
        records.append({
            "ID": idx,
            "CategoryID": category_id,
            "BookLink": book_link,
            "BookTitle": book_title,
            "Sentences": sentences
        })
    
    df = pd.DataFrame(records, columns=["ID", "CategoryID", "BookLink", "BookTitle", "Sentences"])
    return df