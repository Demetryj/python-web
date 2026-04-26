# PW-10 Django Project

Learning Django project with two apps:

- `quotes_app` - quotes, authors, tags, filtering by tag, pagination
- `users_app` - sign up, login, logout, password reset by email

## Stack

- Python + Django
- PostgreSQL
- Docker Compose (local Postgres)
- Poetry (dependency and virtualenv management)

## Project Structure

- `config/` - Django project settings and root URLs
- `quotes_app/` - quote domain logic
- `users_app/` - authentication logic
- `users_app/templates/users_app/password_reset*.html` - password reset pages and email templates
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

4. Create local `.env` from `.env.example` and fill SMTP credentials:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_HOST_USER=<mailtrap-user>
EMAIL_HOST_PASSWORD=<mailtrap-password>
DEFAULT_FROM_EMAIL=no-reply@example.com
```

The project uses Mailtrap SMTP for password reset emails.

5. Run migrations:

```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

6. Optional: import seed data:

```bash
poetry run python utils/filing_db.py
```

7. Run dev server:

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

## Password Reset

Password reset is implemented in `users_app`.

- `ResetPasswordView` renders the email input form and sends reset instructions.
- Django built-in `PasswordResetDoneView` shows the "email sent" page.
- Django built-in `PasswordResetConfirmView` validates `uid` and `token`, then lets the user set a new password.
- Django built-in `PasswordResetCompleteView` shows the final success page.
- Mailtrap SMTP settings are loaded from `.env` in `config/settings.py`.

Templates used by the flow:

- `password_reset.html` - email input form
- `password_reset_email.html` - reset link email body
- `password_reset_subject.txt` - reset email subject
- `password_reset_done.html` - confirmation that email was sent
- `password_reset_confirm.html` - new password form
- `password_reset_complete.html` - final success page

## Main Routes

- `/` - quotes list
- `/author/<id>/` - author page
- `/add-author/` - add author
- `/add-quote/` - add quote
- `/quotes_by_tag/<tag_id>/` - quotes by tag
- `/users/signup/` - sign up
- `/users/login/` - login
- `/users/logout/` - logout
- `/users/reset-password/` - request password reset email
- `/users/reset-password/done/` - password reset email sent page
- `/users/reset-password/confirm/<uidb64>/<token>/` - set new password
- `/users/reset-password/complete/` - password reset completed page
