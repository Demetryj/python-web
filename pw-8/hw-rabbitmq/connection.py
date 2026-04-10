from mongoengine import connect
from mongoengine.connection import get_connection
from pymongo.errors import PyMongoError
import pika
from pika.exceptions import AMQPConnectionError, ProbableAuthenticationError
from typing import Optional

# If a database has already been created in MongoDB Atlas, then for the connection we use:
# connect(host=f"""mongodb+srv://{mongo_user}:{mongodb_pass}@{domain}/{db_name}?retryWrites=true&w=majority""", ssl=True)

def init_mongoDB():
    """Initialize MongoDB connection and verify it with a ping."""
    try:
        connect(
            db="test-hw-rabbitmq",
            host="mongodb://localhost:27017",
            serverSelectionTimeoutMS=3000,
        )
        # Force an immediate round-trip to MongoDB to verify the connection at startup.
        # `connect()` can be lazy, so without this ping, connection errors may appear only on the first real query.
        get_connection().admin.command("ping")
    except PyMongoError as err:
        raise RuntimeError(f"Mongo connection failed: {err}")
    
    
EXCHANGE_NAME_1 = "pw-8-exchange-1"
QUEUE_NAME_1 = "pw_8_queue_1"
    
def init_rabbitMQ():
    """Create and return RabbitMQ blocking connection."""
    try:
        credentials = pika.PlainCredentials('guest', 'guest')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', port=5672, credentials=credentials)
        )
        return connection
    except ProbableAuthenticationError as e:
        print(f"RabbitMQ authorization error: {e}")
    except AMQPConnectionError as e:
        print(f"Unable to connect to RabbitMQ: {e}")
    except Exception as e:
        print(f"Error: {e}")
