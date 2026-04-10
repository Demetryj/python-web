# HW RabbitMQ

Educational project for working with `MongoDB + RabbitMQ` in Python (`pika`, `mongoengine`).

## Project Structure

- `producer.py` - basic producer (single queue).
- `consumer.py` - basic consumer (single queue).
- `producer_mult.py` - producer with routing to multiple queues (`sms` / `email`).
- `consumer_sms.py` - consumer for the `sms` queue.
- `consumer_email.py` - consumer for the `email` queue.
- `connection.py` - connection settings and exchange/queue/routing key constants.
- `models.py` - `Contact` model (including `send_to`).

## Requirements

- Python 3.11+
- Docker (for MongoDB and RabbitMQ)

## Quick Start

1. Start infrastructure services:

```bash
docker compose up -d
```

3. (Optional) Open RabbitMQ Management UI:

- URL: `http://localhost:15672`
- login/password: `guest` / `guest`

4. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Scenario 1: Single Queue

1. Start the consumer:

```bash
python consumer.py
```

2. In another terminal, run the producer:

```bash
python producer.py
```

Result: producer creates contacts, sends `contact_id` messages to RabbitMQ, and consumer marks contacts as sent (`is_sent=True`).

## Scenario 2: Two Queues (sms/email)

1. Start consumers in separate terminals:

```bash
python consumer_sms.py
```

```bash
python consumer_email.py
```

2. In a third terminal, run the producer:

```bash
python producer_mult.py
```

Result: `producer_mult.py` assigns `send_to` (`sms` or `email`) and publishes each message to the correct queue via `routing_key`.

## Configuration

Current local endpoints:

- MongoDB: `mongodb://localhost:27017`
- RabbitMQ: `localhost:5672`

If your Python app runs inside Docker, replace `localhost` with Docker service names from `docker-compose.yaml` (`mongo_db`, `rabbit_mq`).

## Useful Commands

Stop services:

```bash
docker compose down
```

Stop and remove volumes:

```bash
docker compose down -v
```
