"""Import authors, quotes, and tags from JSON files into the Django database.

This script initializes Django ORM, reads `data/authors.json` and
`data/quotes.json`, then performs idempotent upserts:
- authors are upserted by `fullname`
- quotes are upserted by quote text
- tags are created/reused and linked to quotes via ManyToMany
"""

import json
import os
import sys
from functools import wraps
from pathlib import Path

import django
from django.db import transaction

BASE_PATH = Path(__file__).parent.parent.resolve()
# Add the project root to sys.path so app imports work regardless of the
# directory from which this script is executed.
sys.path.insert(0, str(BASE_PATH))
# Explicitly define Django settings for ORM initialization.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# Initialize Django before importing models.
django.setup()

from quotes_app.models import Author, Quote, Tag

authors_file_path = BASE_PATH.joinpath("data/authors.json")
quotes_file_path = BASE_PATH.joinpath("data/quotes.json")


def handle_file_errors(func):
    """Wrap importer functions with JSON/file error handling."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Run wrapped function and print readable file/JSON errors."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as err:
            print(f"File not found: {err}")
            raise
        except json.JSONDecodeError as err:
            print(f"Invalid JSON: {err}")
            raise

    return wrapper


def _read_json(path: Path) -> list[dict]:
    """Read and parse a JSON file into a list of dictionaries."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@handle_file_errors
def insert_author_data():
    """Load authors from JSON and upsert them into the database."""
    # Load all authors from file.
    authors = _read_json(authors_file_path)
    created = 0
    updated = 0

    # One transaction for the whole import:
    # either all author records are applied, or none.
    with transaction.atomic():
        for item in authors:
            # Upsert by unique fullname; update the rest of fields on reruns.
            _, is_created = Author.objects.update_or_create(
                fullname=item["fullname"],
                defaults={
                    "born_date": item["born_date"],
                    "born_location": item["born_location"],
                    "description": item["description"],
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

    print(f"Authors: created={created}, updated={updated}")


@handle_file_errors
def insert_quote_data():
    """Load quotes/tags from JSON and upsert relations in the database."""
    # Load quotes along with their tag lists.
    quotes = _read_json(quotes_file_path)
    created_quotes = 0
    updated_quotes = 0
    created_tags = 0
    updated_tags = 0

    # Transaction for quotes and their many-to-many links.
    with transaction.atomic():
        for item in quotes:
            # Safety fallback: create author if missing.
            # In current dataset all authors should already exist from authors.json.
            author, _ = Author.objects.get_or_create(
                fullname=item["author"],
                defaults={
                    "born_date": "",
                    "born_location": "",
                    "description": "",
                },
            )

            # Upsert by unique quote text.
            quote_obj, is_created = Quote.objects.update_or_create(
                quote=item["quote"],
                defaults={"author": author},
            )

            tag_objects = []
            for tag_name in item.get("tags", []):
                # Create tag if it does not exist yet.
                # If tag exists, count it as reused during this import
                # (not as a row update in the tags table).
                tag_obj, tag_created = Tag.objects.get_or_create(name=tag_name)
                if tag_created:
                    created_tags += 1
                else:
                    updated_tags += 1
                tag_objects.append(tag_obj)

            # Fully synchronize quote tags with JSON.
            # If the list is empty, all existing tag links are cleared.
            quote_obj.tags.set(tag_objects)

            if is_created:
                created_quotes += 1
            else:
                updated_quotes += 1

    print(
        "Quotes: "
        "created="
        f"{created_quotes}, updated={updated_quotes}, "
        f"created_tags={created_tags}, updated_tags={updated_tags}"
    )


def main():
    """Run full data import pipeline: authors first, then quotes/tags."""
    # Order matters: import authors first, then quotes referencing authors.
    insert_author_data()
    insert_quote_data()


if __name__ == "__main__":
    main()
