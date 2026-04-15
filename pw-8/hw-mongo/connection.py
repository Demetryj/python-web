from mongoengine import connect
from mongoengine.connection import get_connection
from pymongo.errors import PyMongoError

# If a database has already been created in MongoDB Atlas, then for the connection we use:
# connect(host=f"""mongodb+srv://{mongo_user}:{mongodb_pass}@{domain}/{db_name}?retryWrites=true&w=majority""", ssl=True)


def init_mongoDB():
    try:
        connect(
            db="test-hw-mongo",
            host="mongodb://localhost:27017",
            serverSelectionTimeoutMS=3000,
        )
        # Force an immediate round-trip to MongoDB to verify the connection at startup.
        # `connect()` can be lazy, so without this ping, connection errors may appear only on the first real query.
        get_connection().admin.command("ping")
    except PyMongoError as e:
        raise RuntimeError(f"Mongo connection failed: {e}")
