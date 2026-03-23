FROM python:3.13-slim

ENV APP_HOME=/app

WORKDIR $APP_HOME

COPY pyproject.toml $APP_HOME/pyproject.toml
COPY poetry.lock $APP_HOME/poetry.lock

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && poetry install --only main --no-root

COPY . .

RUN mkdir -p $APP_HOME/storage
VOLUME ["${APP_HOME}/storage"]

EXPOSE 3000

CMD ["python", "main.py"]