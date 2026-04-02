from psycopg2 import Error
from psycopg2.extensions import connection as PgConnection


def create_table(conn: PgConnection, create_table_sql: str) -> None:
    """ Create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
    """
    try:
        # Get a cursor object from the connection.
        with conn.cursor() as cursor:
            # Execute CREATE TABLE SQL.
            cursor.execute(create_table_sql)
    except Error as error:
        print(error)
        raise
    # Cursor is closed automatically because it was opened via a context manager.
