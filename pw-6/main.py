from psycopg2 import Error

from pathlib import Path

from connection import create_connection
from create_table import create_table

BASE_PATH = Path(__file__).resolve().parent


def main():

    try:
        sql_file = BASE_PATH / "sql_scripts" / "create_tables_script.sql"

        with open(sql_file, "r", encoding="utf-8") as fd:
            rows = fd.read()
    except Exception as err:
        print(err)
        raise

    with create_connection() as connection:
        try:
            # Execute SQL script that creates tables.
            create_table(connection, rows)
            # Commit the transaction if table creation succeeds.
            connection.commit()
        except Error as err:
            # Roll back the transaction if any database error occurs.
            connection.rollback()
            print(err)
            raise


if __name__ == "__main__":
    main()
