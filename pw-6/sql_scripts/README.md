# PW-6: PostgreSQL + Python

An educational project for working with PostgreSQL using `psycopg2`:
- creating tables;
- seeding test data with `Faker`;
- running `SELECT` queries.

## Structure

- `main.py` - reads `sql_scripts/create_tables_script.sql` and creates tables.
- `fill_db_seed.py` - generates and inserts test data (groups, students, teachers, subjects, grades).
- `select_data.py` - helper function for executing `SELECT` queries.
- `connection.py` - PostgreSQL connection via a context manager.
- `sql_scripts/` - SQL scripts for table creation and queries `query_1.sql` ... `query_9.sql`.

## Requirements

- Python 3.11+ (recommended).
- PostgreSQL (local or containerized).

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Database Configuration

Current connection parameters in `connection.py`:
- `database=postgres`
- `user=postgres`
- `password=postgres`
- `host=localhost`
- `port=5432`

Update these values if needed for your environment.

## Run

1. Create/recreate tables:

```bash
python main.py
```

2. Seed the tables with test data:

```bash
python fill_db_seed.py
```

3. Run queries from `sql_scripts/query_*.sql` via psql, or from Python (using `select_data.execute_select_query`).

## Database Diagram

The schema is shown in `postgres_db_chart.png`.
