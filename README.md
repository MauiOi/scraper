Polite Scraper (W5 A9)
Target Classification
Site: https://books.toscrape.com/
Type: Public sandbox for practicing web scraping
Why allowed: The site is explicitly designed for scraping practice
Scope: First 3 catalogue pages only
Total items: 60 books
Data Collected

For each book:

title
product_url
price_gbp (float)
availability (int)
rating (1–5)
description (nullable)
source_page
fetched_at (UTC timestamp)
Robots.txt Check

Visited: https://books.toscrape.com/robots.txt
Result: 404 Not Found

(No robots rules provided by the site)

Ethics Statement

I will not reuse this code on another site without checking its rules and terms first.

How It Works
1. Crawling
Starts from catalogue page 1
Follows “next” links
Stops after 3 pages
Collects 60 unique book URLs


2. Fetching (Polite)
Custom User-Agent
Request timeout
Delay between requests
HTML cached locally


3. Extraction
Uses BeautifulSoup
Extracts raw fields from each book page



4. Normalization
Price converted from "£xx.xx" → float
Availability text → integer
Rating text → numeric value



5. Validation
Uses Pydantic schema
Ensures correct data types
Invalid records stored separately



6. Output
books.json → cleaned valid data (60 records)
errors.json → validation errors (expected: empty)


How to Run;

Install dependencies
python -m pip install requests beautifulsoup4 pydantic
Run scraper
python src/main.py


Output Files;

books.json → validated dataset
errors.json → errors (if any)
/cache → stored HTML pages



Caching Behavior;

First run → fetches pages from the web
Subsequent runs → uses cached HTML
Prevents repeated requests and speeds up execution



Notes;

Script is idempotent (always produces 60 records)
Missing descriptions handled safely
UTF-8 encoding enforced
Provenance tracked via source_page