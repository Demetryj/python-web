# Contacts API (FastAPI + SQLAlchemy + PostgreSQL)

REST API for contacts management with async SQLAlchemy, Alembic migrations,
JWT authentication, email verification, rate limiting, and Docker Compose.

## Features

- User signup and login (`JWT` access + refresh tokens)
- Email verification after signup
- Resend email verification link
- Password reset by email with one-time token validation
- Refresh token rotation
- Logout (refresh token revocation)
- User profile endpoint
- Avatar update through Cloudinary
- Default avatar from Gravatar during signup
- Redis-backed request rate limiting
- Auth-protected contacts endpoints
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
- Redis
- FastAPI-Mail / Mailtrap SMTP
- Cloudinary
- Gravatar
- Poetry
- Docker / Docker Compose

## Environment Variables

Create `.env` in project root (`pw-14`) with:

```env
PSG_DB_USER=postgres
PSG_DB_PASSWORD=postgres
PSG_DB_NAME=contacts
PSG_DB_DOMAIN=db
PSG_DB_PORT=5432

SECRET_KEY=change_me
HASH_ALGORITHM=HS256

MAIL_USERNAME=mailtrap_user
MAIL_PASSWORD=mailtrap_password
MAIL_FROM=test@example.com
MAIL_PORT=2525
MAIL_SERVER=sandbox.smtp.mailtrap.io

REDIS_DOMAIN=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

CLOUDINARY_NAME=cloud_name
CLOUDINARY_API_KEY=12345678
CLOUDINARY_API_SECRET=api_secret
```

For local run (outside Docker), usually set:

```env
PSG_DB_DOMAIN=localhost
REDIS_DOMAIN=localhost
```

Mailtrap is used for email verification messages. Cloudinary is used to upload
and serve user avatars.

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

1. `redis` starts for request rate limiting.
2. `db` starts and becomes healthy.
3. `migrate` runs `alembic upgrade heads`.
4. `fastapi-server` starts only after successful migration.

Useful commands:

```bash
docker compose logs -f
docker compose down
```

## API Routes

### Auth routes

Base prefix: `/api/auth`

- `POST /signup` - create a new user account
- `GET /confirm-email/{token}` - confirm user email by verification token
- `POST /request-email` - resend email verification link
- `POST /password-reset/request` - request password reset email
- `GET /password-reset/verify/{token}` - validate password reset token before showing reset form
- `PATCH /password-reset/confirm` - set a new password using valid reset token
- `POST /signin` - login by username(email) + password, returns `access_token` and `refresh_token`
- `GET /refresh-token` - rotate refresh token and issue a new token pair (requires refresh token in `Authorization: Bearer ...`)
- `POST /logout` - revoke provided refresh token (requires refresh token in `Authorization: Bearer ...`)

Email must be confirmed before signin succeeds.

### User routes

Base prefix: `/api/user`

- `GET /me` - get current authenticated user profile
- `PATCH /update-avatar` - upload avatar image to Cloudinary and save avatar URL

All `/api/user/*` routes require `Authorization: Bearer <access_token>`.

### Contacts routes

Base prefix: `/api/contacts`

- `GET /all?limit=10&offset=0` - list contacts
- `GET /upcoming-birthdays` - contacts with birthdays in the next 7 days
- `GET /{contact_id}` - get one contact
- `GET /?first_name=&last_name=&email=` - search contacts
- `POST /` - create contact
- `PUT /{contact_id}` - full update
- `PATCH /{contact_id}` - partial update
- `DELETE /{contact_id}` - delete contact (204)

All `/api/contacts/*` routes require `Authorization: Bearer <access_token>`.

## Authentication Flow

1. `POST /api/auth/signup` - register a user and send verification email in the background.
2. Open verification link from email: `GET /api/auth/confirm-email/{token}`.
3. `POST /api/auth/signin` - get `access_token` and `refresh_token`.
4. Use `access_token` in `Authorization: Bearer <access_token>` for protected endpoints.
5. When access token expires, call `GET /api/auth/refresh-token` with refresh token in `Authorization` header.
6. To logout, call `POST /api/auth/logout` with refresh token in `Authorization` header.

If verification email is lost, call `POST /api/auth/request-email` with user email.

Password reset flow:

1. `POST /api/auth/password-reset/request` - create a short-lived reset token, store its hash in DB, and send reset email.
2. `GET /api/auth/password-reset/verify/{token}` - validate JWT claims and DB token state before frontend opens reset form.
3. `PATCH /api/auth/password-reset/confirm` - update password and mark reset token as used.

## Email Verification

Email verification is implemented with `fastapi-mail`, Mailtrap SMTP, and a
short-lived JWT email token.

- `src/services/email.py` builds and sends the verification email.
- `src/services/templates/verify_email.html` contains the email HTML template.
- `AuthService.create_email_token()` creates a token with `email_token` scope.
- `GET /api/auth/confirm-email/{token}` validates the token and marks `User.confirmed = True`.
- Unconfirmed users cannot sign in.

## Password Reset

Password reset is implemented with JWT reset tokens plus DB-backed one-time use state.

- `AuthService.create_password_reset_token()` creates a short-lived JWT with `password_reset_token` scope.
- `AuthService.get_token_hash()` stores a deterministic SHA-256 hash of the raw token for DB lookup.
- `AuthService.validate_password_reset_token()` validates JWT claims and checks DB state (`exists`, `used_at is None`, `expires_at > now`).
- `repository_auth.add_password_reset_token()` creates or rotates a single reset token row per user.
- `repository_auth.update_used_status_password_reset_token()` marks token as used after successful password change.
- `repository_users.update_user_password()` writes the new hashed password to the user row.
- `src/services/templates/reset_password.html` contains the reset email template.

Security notes:

- The API returns a generic response from `POST /password-reset/request` even if the email does not exist.
- Reset tokens are validated twice: once before opening the reset form and again before saving the new password.
- A reset token becomes unusable after successful password change because `used_at` is set.

## Rate Limiting

Rate limiters are defined in `src/config/rate_limiters.py` and use Redis
buckets through `pyrate_limiter`.

Current limits:

- Auth base: `60/min`
- Signup: `40/min`
- Refresh token: `50/min`
- Confirm email: `10/min`
- Request verification email: `3/5 min`
- Password reset flow: `5/12 hours`
- Contacts base: `10/min`
- User base: `10/min`
- Avatar update: `1/30 sec`

## Avatars

- During signup, `libgravatar` tries to set a default avatar from the user's email.
- `PATCH /api/user/update-avatar` accepts an uploaded file, sends it to Cloudinary,
  builds a `250x250` cropped image URL, stores it in `User.avatar`, and returns
  the updated user profile.

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
pw-13/fastapi/
  main.py
  docker-compose.yaml
  Dockerfile
  alembic.ini
  src/
    config/settings.py
    config/rate_limiters.py
    database/db.py
    entity/models.py
    repository/auth.py
    repository/contacts.py
    repository/users.py
    routes/auth.py
    routes/contacts.py
    routes/users.py
    schemas/auth.py
    schemas/contacts.py
    schemas/users.py
    services/auth.py
    services/email.py
    services/templates/verify_email.html
    services/templates/reset_password.html
    migrations/
```
