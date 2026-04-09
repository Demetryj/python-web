# HW Mongo Quotes CLI

Simple console app for searching quotes in MongoDB with optional Redis cache.

## Features

- `name:<author_name>`: find all quotes by author name (supports partial input, e.g. `name:st`)
- `tag:<tag_name>`: find quotes by one tag (supports partial input, e.g. `tag:li`)
- `tags:<tag1>,<tag2>`: find quotes where any listed tag exists
- `exit`: stop the app

## Project Files

- `main.py` - CLI entry point
- `connection.py` - MongoDB connection setup
- `models.py` - MongoEngine models (`Author`, `Quote`)
- `seeds.py` - import seed data into MongoDB
- `docker-compose.yaml` - MongoDB + Redis services

## Requirements

- Python 3.11+
- Docker + Docker Compose

Python packages (from `requirements.txt`):

- `mongoengine==0.29.3`
- `pymongo==4.16.0`
- `redis==7.4.0`
- `redis-lru==0.1.2`

## Quick Start

1. Start infrastructure:

```bash
docker compose up -d
```

2. Create and activate virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
```

PowerShell alternative:

```powershell
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Seed database (one-time or when needed):

```bash
python seeds.py
```

5. Run CLI app:

```bash
python main.py
```

## Usage Examples

```text
>>> Enter a command: name:Steve Martin
>>> Enter a command: name:st
>>> Enter a command: tag:life
>>> Enter a command: tag:li
>>> Enter a command: tags:life,live
>>> Enter a command: exit
```

## Notes

- `name:` and `tag:` with empty value return an empty list.
- App expects MongoDB on `localhost:27017` and Redis on `localhost:6379`.
- Stop services with:

```bash
docker compose down
```
