# PW-10 Django Project

Learning Django project with two apps:

- `quotes_app` - quotes, authors, tags, filtering by tag, pagination
- `users_app` - sign up, login, logout

## Stack

- Python + Django
- PostgreSQL
- Docker Compose (local Postgres)
- Poetry (dependency and virtualenv management)

## Project Structure

- `config/` - Django project settings and root URLs
- `quotes_app/` - quote domain logic
- `users_app/` - authentication logic
- `data/` - `authors.json`, `quotes.json`
- `utils/filing_db.py` - JSON -> DB import script

## Quick Start (Bash)

1. Start PostgreSQL:

```bash
docker compose up -d
```

2. Install Poetry (if not installed):

```bash
pip install poetry
```

3. Install dependencies:

```bash
poetry install
```

4. Run migrations:

```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

5. Optional: import seed data:

```bash
poetry run python utils/filing_db.py
```

6. Run dev server:

```bash
poetry run python manage.py runserver
```

## Useful Commands

### Migrations

```bash
poetry run python manage.py showmigrations
poetry run python manage.py makemigrations
poetry run python manage.py migrate
poetry run python manage.py sqlmigrate quotes_app 0001
```

### Create a new app

```bash
poetry run python manage.py startapp <app_name>
```

After that, add the app to `INSTALLED_APPS` in `config/settings.py`.

### Admin user

```bash
poetry run python manage.py createsuperuser
```

### Project checks

```bash
poetry run python manage.py check
```

### Django shell

```bash
poetry run python manage.py shell
```

## Database Notes

Database configuration is defined in `config/settings.py` (`DATABASES`).
Use your own local values (do not commit real credentials).

## Main Routes

- `/` - quotes list
- `/author/<id>/` - author page
- `/add-author/` - add author
- `/add-quote/` - add quote
- `/quotes_by_tag/<tag_id>/` - quotes by tag
- `/users/signup/` - sign up
- `/users/login/` - login
- `/users/logout/` - logout
