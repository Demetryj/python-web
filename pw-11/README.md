# Contacts API (FastAPI + SQLAlchemy + PostgreSQL)

REST API for contacts management with async SQLAlchemy, Alembic migrations, and Docker Compose.

## Features

- Create a contact
- Get all contacts (pagination)
- Get contact by id
- Update contact (PUT/PATCH)
- Delete contact
- Search contacts by `first_name`, `last_name`, or `email`
- Get contacts with upcoming birthdays for the next 7 days

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.x (async)
- Alembic
- PostgreSQL 16
- Poetry
- Docker / Docker Compose

## Environment Variables

Create `.env` in project root (`pw-11`) with:

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=contacts_db
DB_DOMAIN=db
DB_PORT=5432
SECRET_KEY=change_me
```

For local run (outside Docker), usually set:

```env
DB_DOMAIN=localhost
```

## Run Locally (Poetry)

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn main:app --reload
```

API:

- App: `http://127.0.0.1:8000`
- Docs:
  - `http://127.0.0.1:8000/docs` (Swagger)
  - `http://127.0.0.1:8000/openapi.json`
  - `http://127.0.0.1:8000/redoc`

## Run with Docker Compose

```bash
docker compose up --build -d
```

Current compose flow:

1. `db` starts and becomes healthy
2. `migrate` runs `alembic upgrade head`
3. `fastapi-server` starts only after successful migration

Useful commands:

```bash
docker compose logs -f
docker compose down
```

## API Routes

Base prefix: `/api/contacts`

- `GET /all?limit=10&offset=0` - list contacts
- `GET /upcoming-birthdays` - contacts with birthdays in the next 7 days
- `GET /{contact_id}` - get one contact
- `GET /?first_name=&last_name=&email=` - search contacts
- `POST /` - create contact
- `PUT /{contact_id}` - full update
- `PATCH /{contact_id}` - partial update
- `DELETE /{contact_id}` - delete contact (204)

## Data Validation Notes

- `phone_number` uses `PhoneNumber` (`pydantic_extra_types`) and should be in international format (example: `+380671234567`)
- `birth_date` input is accepted in `DD-MM-YYYY` (example: `20-04-2026`)
- response `birth_date` is serialized to `DD-MM-YYYY`
- request validation errors are returned as `400` (custom global handler), not default `422`

## Migrations

- Local (without Docker):

```bash
poetry run alembic revision --autogenerate -m "message"
poetry run alembic upgrade head
```

- Docker Compose:

- Migration is applied automatically by `migrate` service during:

```bash
docker compose up --build -d
```

### If you changed SQLAlchemy model(s)

- Local flow:

```bash
poetry run alembic revision --autogenerate -m "update contacts model"
poetry run alembic upgrade head
poetry run uvicorn main:app --reload
```

- Docker flow:

```bash
docker compose down -v
docker compose up --build -d
docker compose logs -f migrate
docker compose logs -f fastapi-server
```

## Project Structure

```text
pw-11/
  main.py
  docker-compose.yaml
  Dockerfile
  alembic.ini
  src/
    config/settings.py
    database/db.py
    entity/contacts/models.py
    repository/contacts.py
    routes/contacts.py
    schemas/contacts.py
    migrations/
```
