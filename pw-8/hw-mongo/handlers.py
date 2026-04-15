import json
from functools import wraps

from mongoengine.errors import NotUniqueError, ValidationError
from pymongo.errors import PyMongoError


def handle_file_errors(func):
    """Catch file access and JSON parsing errors for importer functions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Execute the wrapped function and re-raise file-related exceptions."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as err:
            print(f"File not found: {err}")
            raise
        except json.JSONDecodeError as err:
            print(f"Invalid JSON: {err}")
            raise

    return wrapper


def handle_db_errors(func):
    """Catch and report MongoDB and MongoEngine-related write/read errors."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Execute the wrapped function and re-raise database exceptions."""
        try:
            return func(*args, **kwargs)
        except NotUniqueError as err:
            print(f"Duplicate key error: {err}")
            raise
        except ValidationError as err:
            print(f"Validation error: {err}")
            raise
        except PyMongoError as err:
            print(f"MongoDB error: {err}")
            raise

    return wrapper
