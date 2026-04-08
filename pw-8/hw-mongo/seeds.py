import json
from pathlib import Path

from mongoengine.connection import get_db

from connection import init_mongoDB
from models import Author, Quote
from handlers import handle_db_errors, handle_file_errors



BASE_PATH = Path(__file__).parent.resolve()

authors_file_path = BASE_PATH.joinpath("data/authors.json")
quotes_file_path = BASE_PATH.joinpath("data/quotes.json")


collection_authors = "authors"
collection_quotes = "quotes"


@handle_file_errors
@handle_db_errors
def insert_author_data():
    """Load authors from JSON and insert them into the authors collection."""
    with open(authors_file_path, "r", encoding="utf-8") as fd:
        data = json.load(fd)
        for el in data:
            author = Author(
                fullname=el.get("fullname"),
                born_date=el.get("born_date"),
                born_location=el.get("born_location"),
                description=el.get("description"),
            )
            author.save()


@handle_file_errors
@handle_db_errors
def insert_quote_data():
    """Load quotes from JSON and link each quote to an existing author."""
    with open(quotes_file_path, "r", encoding="utf-8") as fd:
        data = json.load(fd)
                
        for el in data:
            author = Author.objects(fullname=el.get("author")).first()
            if not author:
                print(f'Author "{el.get("author")}" not found, skipped.')
                continue
        
            quote = Quote(
                author=author,
                tags=el.get("tags",[]),
                quote=el.get("quote"),
                
                
            )
            quote.save()


if __name__ == "__main__":
    # connecting to BD
    init_mongoDB()
    
    db = get_db()
    
    if collection_authors in db.list_collection_names():
        # Author.drop_collection()
        Author.objects().delete()
    if collection_quotes in db.list_collection_names():
        # Quote.drop_collection()
        Quote.objects().delete()
    
    
    insert_author_data()
    insert_quote_data()
    
