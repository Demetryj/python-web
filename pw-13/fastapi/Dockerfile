FROM python:3.13-slim

# Active variant: Docker Compose controls startup order and runs
# migration/app commands via `command` in docker-compose.yaml.
# This image only installs dependencies and application code.
ENV APP_HOME=/app \
    POETRY_VERSION=2.3.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR $APP_HOME

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && poetry install --only main --no-root

COPY . .
EXPOSE 8000



# Alternative variant (kept as reference):
# Use a dedicated run.sh as container entrypoint.
# In that mode, run.sh usually waits for DB, runs migrations,
# and then starts uvicorn from inside one startup script.
# FROM python:3.13-slim

# ENV APP_HOME=/app

# WORKDIR $APP_HOME

# RUN apt-get update \
#     && apt-get install --no-install-recommends -y \
#         # deps for installing poetry
#         curl \
#         # deps for building python deps
#         build-essential \
#         libpq-dev \
#         postgresql-client

# # Environment variables to configure Poetry
# ENV POETRY_VERSION=2.3.2 \
#     POETRY_HOME="/opt/poetry" \
#     POETRY_VIRTUALENVS_CREATE=false \
#     POETRY_NO_INTERACTION=1

# RUN curl -sSL https://install.python-poetry.org | python3 - && \
#     ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry


# COPY poetry.lock pyproject.toml /app/

# RUN poetry install --no-root --no-interaction --no-ansi --verbose

# COPY . .

# EXPOSE 8000

# RUN chmod +x /app/run.sh

# CMD ["sh", "./run.sh"]
