# Quotes Scraper (`beautiful_soup`)

A small scraper for <https://quotes.toscrape.com/> built with `requests` and `BeautifulSoup`.
It collects all quotes across paginated pages and saves data into JSON files.

## Features

- Fetches all quote pages (`next` pagination)
- Collects quote text, author name, and tags
- Collects author profile data from author pages
- Deduplicates authors across all pages
- Uses one `requests.Session()` for faster repeated requests
- Handles network/HTML/file errors without crashing

## Project Structure

- `main.py` - scraper entry point and parsing logic
- Output files are created in `../data/`:
  - `authors.json`
  - `quotes.json`

Resolved paths from code:

- `pw-9/data/authors.json`
- `pw-9/data/quotes.json`

## Requirements

From `pw-9/Pipfile`:

- Python `3.13`
- `requests==2.33.1`
- `beautifulsoup4==4.14.3`

## Installation

From `pw-9`:

```bash
pipenv install
```

## Run

From `pw-9`:

```bash
pipenv run python beautiful_soup/main.py
```

Expected console flow:

- `Scraping started`
- `Data successfully written to files.`

If a request fails, the script prints the error and continues safely.

## Notes

- The scraper expects HTTP `200` as a successful response.
- Parent output directory is created automatically if it does not exist.
- Author name normalization includes:
  - `Alexandre Dumas` -> `Alexandre Dumas-fils`
