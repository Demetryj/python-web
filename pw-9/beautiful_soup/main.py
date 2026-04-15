import json
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SCRAP_URL = "https://quotes.toscrape.com/"

BASE_PATH = Path(__file__).parent.parent.resolve()  # /pw-9
AUTHORS_FILE_PATH = BASE_PATH.joinpath("data/authors.json")
QUOTES_FILE_PATH = BASE_PATH.joinpath("data/quotes.json")


def fetch(
    session: requests.Session, url: str, timeout: int = 10
) -> requests.Response | None:
    """Fetch URL and return response only for HTTP 200; otherwise return None."""
    try:
        response = session.get(url, timeout=timeout)
        if response.status_code == 200:
            return response

        print(f"Status {response.status_code} for {url}")
        return None
    except requests.RequestException as err:
        print(f"Request failed for {url}: {err}")
        return None


def parse_author_data(
    session: requests.Session, page_link: str, base_url: str
) -> dict[str, str] | None:
    """Parse author details page and return normalized author data."""
    html_doc = fetch(session, urljoin(base_url, page_link))
    if html_doc is None:
        return None

    soup = BeautifulSoup(html_doc.content, "html.parser")

    fullname = soup.find("h3", class_="author-title")
    born_date = soup.find("span", class_="author-born-date")
    born_location = soup.find("span", class_="author-born-location")
    description = soup.find("div", class_="author-description")

    if not all([fullname, born_date, born_location, description]):
        print(f"Author page has unexpected structure: {page_link}")
        return None

    return {
        "fullname": fullname.text.strip(),
        "born_date": born_date.text.strip(),
        "born_location": born_location.text.strip(),
        "description": description.text.strip(),
    }


def parse_data(
    session: requests.Session,
    html_doc: requests.Response | None,
    base_url: str,
    seen_author_links: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], str | None]:
    """Parse one quotes page and return page quotes, new authors and next page link."""
    if html_doc is None:
        return [], [], None

    soup = BeautifulSoup(html_doc.content, "html.parser")

    quote_list: list[dict[str, Any]] = []
    author_list: list[dict[str, str]] = []

    # Collect quotes from the current page and parse authors in parallel.
    for quote_item in soup.select("div.quote"):
        author = quote_item.find("small", attrs={"class": "author"})
        quote = quote_item.find("span", class_="text")
        tags = [tag.text.strip() for tag in quote_item.find_all("a", class_="tag")]

        if author is None or quote is None:
            continue

        author_name = author.text.strip()
        if "Alexandre Dumas" in author_name:
            author_name = "Alexandre Dumas-fils"

        about_author_tag = author.find_next_sibling("a")
        if about_author_tag is None or "href" not in about_author_tag.attrs:
            continue

        about_author_link = about_author_tag["href"]

        quote_list.append(
            {
                "author": author_name,
                "quote": quote.text.strip(),
                "tags": tags,
            }
        )

        # Add each author only once based on the author page link.
        if about_author_link not in seen_author_links:
            author_data = parse_author_data(session, about_author_link, base_url)
            if author_data is not None:
                author_list.append(author_data)
                seen_author_links.add(about_author_link)

    # Extract relative link to the next page in pagination.
    next_page_link: str | None = None
    link_next = soup.find("li", class_="next")
    if link_next:
        next_anchor = link_next.find("a")
        if next_anchor and "href" in next_anchor.attrs:
            next_page_link = next_anchor["href"]

    return quote_list, author_list, next_page_link


def write_in_file(file_path: Path, data: list[dict[str, Any]]) -> bool:
    """Create parent directory if needed and save data as JSON."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as fd:
            json.dump(data, fd, ensure_ascii=False, indent=4)
        return True
    except (OSError, TypeError, ValueError) as err:
        print(f"Failed to write file {file_path}: {err}")
        return False


def main() -> None:
    """Run full scraping flow across all paginated quote pages."""
    print("Scraping started")
    quotes: list[dict[str, Any]] = []
    authors: list[dict[str, str]] = []
    seen_author_links: set[str] = set()
    next_page_url: str | None = SCRAP_URL

    # Reuse one HTTP session for all requests to reduce connection overhead.
    with requests.Session() as session:
        # Iterate through all pages while a next-page link exists.
        while next_page_url:
            html_doc = fetch(session, next_page_url)
            if html_doc is None:
                print(f"Cannot fetch page: {next_page_url}")
                break

            # Parse current page and accumulate results.
            page_quotes, page_authors, next_page_link = parse_data(
                session, html_doc, SCRAP_URL, seen_author_links
            )
            quotes.extend(page_quotes)
            authors.extend(page_authors)

            # Build absolute URL for the next page.
            next_page_url = (
                urljoin(SCRAP_URL, next_page_link) if next_page_link else None
            )

    # Save final collections into JSON files.
    quotes_ok = write_in_file(QUOTES_FILE_PATH, quotes)
    authors_ok = write_in_file(AUTHORS_FILE_PATH, authors)

    if not (quotes_ok and authors_ok):
        print("Completed with write errors.")
    else:
        print("Data successfully written to files.")


if __name__ == "__main__":
    main()
