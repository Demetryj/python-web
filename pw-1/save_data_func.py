from pickle import dump, load
from pathlib import Path

from _classes import AddressBook

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FILE = BASE_DIR / "addressbook.pkl"

def save_data(book: AddressBook, filename:str = DEFAULT_FILE) -> None:
    """Serialization of the contacts object (contact book)"""
    with open(filename, 'wb') as fh:
        dump(book, fh)
        
def load_data(filename:str = DEFAULT_FILE) -> AddressBook:
    """Deserialization of the contacts object (contact book)"""
    try:
        with open(filename, "rb") as fh:
            return load(fh)
    except FileNotFoundError:
        return AddressBook()
    
