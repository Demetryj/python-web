import psycopg2
from psycopg2 import DatabaseError

from contextlib import contextmanager

DATABASE = "postgres"
USER = "postgres"
PASSWORD = "postgres"
HOST = "localhost"
PORT = 5432


@contextmanager
def create_connection(
    database: str = DATABASE,
    user: str = USER,
    password: str = PASSWORD,
    host: str = HOST,
    port: int = PORT,
):
    """Create a database connection to a PostgreSQL database"""

    connection = None

    try:
        connection = psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        yield connection
    except DatabaseError:
        raise
    finally:
        if connection is not None:
            connection.close()
