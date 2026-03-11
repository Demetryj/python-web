
FROM python:3.13-slim

ENV APP_HOME=/app

WORKDIR ${APP_HOME}

COPY Pipfile Pipfile.lock ./
RUN pip install --no-cache-dir pipenv && pipenv verify && pipenv sync --system

COPY . .

CMD ["python", "main.py"]
