import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, UTC
from pydantic import BaseModel, ValidationError
import json
import re


class Book(BaseModel):
    title: str
    product_url: str
    price_gbp: float
    availability: int
    rating: int
    description: str | None
    source_page: str
    fetched_at: str


BASE_URL = "https://books.toscrape.com/"
CACHE_DIR = "cache"

HEADERS = {"User-Agent": "PoliteScraper/1.0 (learning project)"}

TIMEOUT = 5
DELAY = 0.5


def fetch_page(url, cache_name):
    cache_path = os.path.join(CACHE_DIR, cache_name)

    if os.path.exists(cache_path):
        print(f"CACHE HIT: {cache_name}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    print(f"FETCH: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.encoding = "utf-8"  # ADD THIS
        if response.status_code != 200:
            print(f"Failed: {response.status_code}")
            return None

        html = response.text

        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(html)

        time.sleep(DELAY)  # polite delay
        return html

    except requests.exceptions.Timeout:
        print("Timeout")
        return None


def extract_book_links(html, page_url):
    soup = BeautifulSoup(html, "html.parser")

    links = []

    articles = soup.select("article.product_pod h3 a")

    for a in articles:
        href = a.get("href")
        absolute_url = urljoin(page_url, href)
        links.append(absolute_url)

    return links


def discover_all_books():
    all_urls = []  # now holds (url, source_page) tuples
    visited_pages = 0

    current_url = urljoin(BASE_URL, "catalogue/page-1.html")

    while current_url and visited_pages < 3:
        cache_name = f"catalogue-page-{visited_pages+1}.html"
        html = fetch_page(current_url, cache_name)

        if not html:
            break

        links = extract_book_links(html, current_url)
        all_urls.extend(
            (link, current_url) for link in links
        )  # pair each link with its page

        soup = BeautifulSoup(html, "html.parser")
        next_btn = soup.select_one("li.next a")

        if next_btn:
            next_href = next_btn.get("href")
            current_url = urljoin(current_url, next_href)
        else:
            current_url = None

        visited_pages += 1

    unique_urls = list(
        set(all_urls)
    )  # dedupes on (url, source_page) tuples — fine, tuples are hashable

    print(f"catalogue_pages={visited_pages}")
    print(f"discovered={len(all_urls)}")
    print(f"unique_urls={len(unique_urls)}")

    return unique_urls


def main():
    urls = discover_all_books()

    valid_books = []
    errors = []

    for i, (url, source_page) in enumerate(urls):
        html = fetch_page(url, f"book-{i}.html")

        if not html:
            continue

        raw = extract_book_data(html, url, source_page)

        try:
            normalized = normalize_record(raw)
            book = Book(**normalized)
            valid_books.append(book.dict())
        except ValidationError as e:
            errors.append({"url": url, "error": str(e)})

    print(f"valid={len(valid_books)} errors={len(errors)}")

    with open("books.json", "w", encoding="utf-8") as f:
        json.dump(valid_books, f, indent=2, ensure_ascii=False)

    with open("errors.json", "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2)


def extract_book_data(html, url, source_page):
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title = soup.select_one("div.product_main h1").text.strip()

    # Price
    price_text = soup.select_one(".price_color").text.strip()

    # Availability
    availability_text = soup.select_one(".availability").text.strip()

    # Rating (stored as class like "star-rating Three")
    rating_element = soup.select_one(".star-rating")
    rating_text = rating_element.get("class")[1] if rating_element else None

    # Description (can be missing!)
    desc_element = soup.select_one("#product_description + p")
    description = desc_element.text.strip() if desc_element else None

    return {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(UTC).isoformat(),
    }


def normalize_record(raw):
    # Price: "£14.27" → 14.27
    price = float(raw["price_text"].replace("£", ""))

    # Availability: extract number
    match = re.search(r"\d+", raw["availability_text"])
    availability = int(match.group()) if match else 0

    # Rating: text → number
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    rating = rating_map.get(raw["rating_text"], 0)

    return {
        "title": raw["title"],
        "product_url": raw["product_url"],
        "price_gbp": price,
        "availability": availability,
        "rating": rating,
        "description": raw["description"],
        "source_page": raw["source_page"],
        "fetched_at": raw["fetched_at"],
    }


if __name__ == "__main__":
    main()
