
# Базовий образ з Python 3.13 (полегшена версія)
FROM python:3.13-slim

# Змінна з шляхом до директорії застосунку
ENV APP_HOME=/app

# Переходимо в робочу директорію контейнера
WORKDIR ${APP_HOME}

# Копіюємо файли залежностей
COPY Pipfile Pipfile.lock ./
# Встановлюємо pipenv, перевіряємо lock-файл і ставимо залежності в system
RUN pip install --no-cache-dir pipenv && pipenv verify && pipenv sync --system

# Копіюємо весь код проєкту в контейнер
COPY . .

# Команда запуску застосунку
CMD ["python", "main.py"]
