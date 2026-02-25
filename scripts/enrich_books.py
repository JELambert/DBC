#!/usr/bin/env python3
"""
Book enrichment script for the Drunk Book Club dashboard.

Queries Open Library API and Google Books API to fetch metadata for each book,
then outputs a structured JSON file for use in the Streamlit dashboard.

Usage:
    python enrich_books.py                          # uses default CSV path
    python enrich_books.py --csv path/to/file.csv   # custom CSV path
    python enrich_books.py --output path/to/out.json # custom output path
"""

import argparse
import csv
import json
import os
import sys
import time
from urllib.parse import quote

import requests

# Defaults relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(SCRIPT_DIR, "..", "DrunkBookClub - Sheet1.csv")
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "..", "data", "book_enrichment.json")

# API endpoints
OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
GOOGLE_BOOKS_SEARCH = "https://www.googleapis.com/books/v1/volumes"

# Rate limiting
REQUEST_DELAY = 1.0  # seconds between API calls
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def fetch_with_retry(url, params=None, retries=MAX_RETRIES):
    """Fetch a URL with retry logic and exponential backoff."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt < retries - 1:
                wait = RETRY_BACKOFF ** (attempt + 1)
                print(f"  Retry {attempt + 1}/{retries} after {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"  Failed after {retries} attempts: {e}")
                return None


def search_open_library(title, author=None):
    """Search Open Library for a book and return metadata."""
    params = {"title": title, "limit": 5}
    if author:
        params["author"] = author

    data = fetch_with_retry(OPEN_LIBRARY_SEARCH, params=params)
    if not data or not data.get("docs"):
        return {}

    # Pick the best match (first result)
    doc = data["docs"][0]

    result = {}
    result["full_title"] = doc.get("title", title)
    result["author"] = ", ".join(doc.get("author_name", [])) or author or "Unknown"
    result["publication_year"] = doc.get("first_publish_year")

    # ISBN - prefer ISBN-13
    isbns = doc.get("isbn", [])
    isbn_13 = [i for i in isbns if len(i) == 13]
    result["isbn"] = isbn_13[0] if isbn_13 else (isbns[0] if isbns else "")

    if result["isbn"]:
        result["cover_url"] = f"https://covers.openlibrary.org/b/isbn/{result['isbn']}-L.jpg"
    else:
        cover_id = doc.get("cover_i")
        if cover_id:
            result["cover_url"] = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        else:
            result["cover_url"] = ""

    result["pages"] = doc.get("number_of_pages_median", 0)
    result["subjects"] = doc.get("subject", [])[:10]

    return result


def search_google_books(title, author=None):
    """Search Google Books for a book and return metadata."""
    query = f'intitle:{title}'
    if author:
        query += f'+inauthor:{author}'

    params = {"q": query, "maxResults": 3}
    data = fetch_with_retry(GOOGLE_BOOKS_SEARCH, params=params)
    if not data or not data.get("items"):
        return {}

    vol = data["items"][0].get("volumeInfo", {})

    result = {}
    result["full_title"] = vol.get("title", title)
    result["subtitle"] = vol.get("subtitle", "")
    result["author"] = ", ".join(vol.get("authors", []))
    result["publication_year"] = vol.get("publishedDate", "")[:4]
    result["pages"] = vol.get("pageCount", 0)
    result["genres"] = vol.get("categories", [])
    result["description"] = vol.get("description", "")

    # ISBN from industry identifiers
    identifiers = vol.get("industryIdentifiers", [])
    isbn_13 = [i["identifier"] for i in identifiers if i.get("type") == "ISBN_13"]
    isbn_10 = [i["identifier"] for i in identifiers if i.get("type") == "ISBN_10"]
    result["isbn"] = isbn_13[0] if isbn_13 else (isbn_10[0] if isbn_10 else "")

    return result


def merge_results(title, ol_data, gb_data):
    """Merge Open Library and Google Books data into the final schema."""
    book = {
        "full_title": ol_data.get("full_title") or gb_data.get("full_title") or title,
        "author": ol_data.get("author") or gb_data.get("author") or "Unknown",
        "publication_year": ol_data.get("publication_year") or gb_data.get("publication_year") or 0,
        "genres": gb_data.get("genres", []) or [],
        "pages": ol_data.get("pages") or gb_data.get("pages") or 0,
        "isbn": ol_data.get("isbn") or gb_data.get("isbn") or "",
        "cover_url": ol_data.get("cover_url") or "",
        "plot_summary": gb_data.get("description", "")[:300] if gb_data.get("description") else "",
        "fun_facts": [],
        "awards": [],
        "goodreads_url": "",
        "goodreads_rating": 0,
        "themes": [],
        "mood": "",
        "difficulty": "moderate",
    }

    # Build cover URL from ISBN if not already set
    if not book["cover_url"] and book["isbn"]:
        book["cover_url"] = f"https://covers.openlibrary.org/b/isbn/{book['isbn']}-L.jpg"

    return book


def read_book_titles(csv_path):
    """Read book titles from the CSV file."""
    titles = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("Book", "").strip()
            if title:
                titles.append(title)
    return titles


def main():
    parser = argparse.ArgumentParser(description="Enrich book data from APIs")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to the input CSV file")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to the output JSON file")
    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv)
    output_path = os.path.abspath(args.output)

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    titles = read_book_titles(csv_path)
    print(f"Found {len(titles)} books in CSV")

    # Load existing enrichment data if present (to avoid re-fetching)
    existing = {}
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
                print(f"Loaded {len(existing)} existing entries from {output_path}")
            except json.JSONDecodeError:
                existing = {}

    enrichment = {}
    for i, title in enumerate(titles, 1):
        print(f"\n[{i}/{len(titles)}] Processing: {title}")

        # Skip if we already have enrichment data with a valid ISBN
        if title in existing and existing[title].get("isbn"):
            print(f"  Using existing data (ISBN: {existing[title]['isbn']})")
            enrichment[title] = existing[title]
            continue

        # Query APIs
        print(f"  Querying Open Library...")
        ol_data = search_open_library(title)
        time.sleep(REQUEST_DELAY)

        print(f"  Querying Google Books...")
        gb_data = search_google_books(title)
        time.sleep(REQUEST_DELAY)

        # Merge results
        book = merge_results(title, ol_data, gb_data)
        enrichment[title] = book
        print(f"  -> {book['full_title']} by {book['author']} ({book['publication_year']})")
        print(f"     ISBN: {book['isbn']} | Pages: {book['pages']}")

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enrichment, f, indent=2, ensure_ascii=False)

    print(f"\nWrote enrichment data for {len(enrichment)} books to {output_path}")


if __name__ == "__main__":
    main()
