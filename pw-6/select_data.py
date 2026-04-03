from psycopg2 import Error

from connection import create_connection

Row = tuple[object, ...]

            
def execute_select_query(sql: str, params: tuple | list | dict | None = None) -> list[Row]:
    """Execute a SELECT query and return all fetched rows."""
    
    with create_connection() as connection:
        try:
            with connection.cursor() as cursor:
                if params is None:
                    cursor.execute(sql)
                else:
                    cursor.execute(sql, params)
                return cursor.fetchall()
        except Error as err:
            connection.rollback()
            print(err)
            raise
