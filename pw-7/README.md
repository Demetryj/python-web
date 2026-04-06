# PW-7: SQLAlchemy ORM + Alembic + PostgreSQL

An educational project for working with PostgreSQL using SQLAlchemy ORM.
The project includes:
- ORM models for an educational domain (groups, students, teachers, subjects, grades);
- schema management with Alembic;
- a seed script for generating test data (Faker);
- a set of analytical queries `select_1 ... select_12`.

## Project Structure

- `conf/models.py` - models `Group`, `Student`, `Teacher`, `Subject`, `Grade`, relationships, and constraints.
- `conf/db.py` - reads `config.ini`, creates `engine`, session factory `DBsession`, and context manager `get_session()`.
- `repository/my_select.py` - query functions `select_1 ... select_12`.
- `seeds/seed.py` - table cleanup (`TRUNCATE ... RESTART IDENTITY CASCADE`) and test data seeding.
- `main.py` - dynamic query execution via `run_query(n, session, **kwargs)`.
- `alembic/`, `alembic.ini` - migrations and Alembic configuration.
- `config.ini` - database connection parameters (`[DEV_DB]`).

## Requirements

- Python 3.13+
- PostgreSQL

## Installation

```bash
poetry install
```

## Database Configuration

Fill in the `[DEV_DB]` section in `config.ini`:
- `USER`
- `PASSWORD`
- `DOMAIN`
- `PORT`
- `DB_NAME`

## Migrations

```bash
poetry run alembic upgrade head
```

## Seed Data

```bash
poetry run python -m seeds.seed
```

Seed script behavior:
- clears tables before inserting new data;
- resets `id` sequences (`RESTART IDENTITY`);
- repeated runs do not accumulate duplicate old data.

## Running Queries

`main.py` executes a query by number:
- `run_query(n=..., session=..., **kwargs)` looks up function `select_N` in `repository/my_select.py`.

Current example in `main.py`:
- runs `select_12` with parameters `group` and `discipline`.

Typical query parameters:
- `discipline` - subject name;
- `group` - group name;
- `student` - student full name (`"FirstName LastName"`);
- `lector` - teacher full name (`"FirstName LastName"`).

## Query List

- `select_1` - top 5 students by average grade.
- `select_2` - student with the highest average in a specific subject.
- `select_3` - average grade by groups for a specific subject.
- `select_4` - average grade across the whole grades table.
- `select_5` - subjects taught by a specific teacher.
- `select_6` - list of students in a specific group.
- `select_7` - grades of students in a group for a specific subject.
- `select_8` - average grade given by a specific teacher.
- `select_9` - list of subjects taken by a specific student.
- `select_10` - subjects taught by a specific teacher to a specific student.
- `select_11` - average grade a specific teacher gives to a specific student.
- `select_12` - students' grades in a group for a subject on the last lesson date.

## Important

Run modules from the `pw-7` root:
- correct: `poetry run python -m seeds.seed`
- correct: `poetry run python -m main`

This is required for imports to work correctly.
