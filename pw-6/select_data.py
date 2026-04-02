from psycopg2 import Error

from connection import create_connection

Row = tuple[object, ...]


def execute_select_query(sql: str) -> list[Row]:
    """Execute a SELECT query and return all fetched rows."""
    with create_connection() as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                return cursor.fetchall()
        except Error as err:
            connection.rollback()
            print(err)
            raise
            
