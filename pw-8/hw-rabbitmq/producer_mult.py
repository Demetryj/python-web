from random import choice

from mongoengine.errors import NotUniqueError, ValidationError
import pika
from pika.exceptions import AMQPConnectionError
from pymongo.errors import PyMongoError
from faker import Faker

from models import Contact
from connection import (
    init_mongoDB,
    init_rabbitMQ,
    EXCHANGE_NAME_2,
    QUEUE_NAME_SMS,
    QUEUE_NAME_EMAIL,
    ROUTING_KEY_SMS,
    ROUTING_KEY_EMAIL,
)

fake = Faker("en_US")

NUMBER_CONTACTS = 100


def insert_contacts() -> str:
    """Create and store a batch of fake contacts in MongoDB."""
    try:
        for _ in range(NUMBER_CONTACTS):
            contact = Contact(
                fullname=fake.name(),
                email=fake.email(),
                phone=fake.phone_number()[:25],
                address=fake.address()[:120],
                is_sent=False,
                send_to=choice([ROUTING_KEY_SMS, ROUTING_KEY_EMAIL])
            )
            contact.save()
        return "Ok"
    except NotUniqueError as err:
        print(f"Duplicate key error: {err}")
        raise
    except ValidationError as err:
        print(f"Validation error: {err}")
        raise
    except PyMongoError as err:
        print(f"MongoDB error: {err}")
        raise


def main():
    init_mongoDB()
    Contact.objects().delete()  # Clear collection if it already contains data.
    insert_contacts()

    connection = None
    try:
        # Connect to RabbitMQ and prepare exchange/queue.
        connection = init_rabbitMQ()
        channel = connection.channel()
        
        # Creating two queues and binding them to the exchange
        channel.exchange_declare(
            exchange=EXCHANGE_NAME_2, exchange_type="direct", durable=True
        )
        channel.queue_declare(queue=QUEUE_NAME_SMS, durable=True)
        channel.queue_declare(queue=QUEUE_NAME_EMAIL, durable=True)

        channel.queue_bind(
            exchange=EXCHANGE_NAME_2, queue=QUEUE_NAME_SMS, routing_key="sms"
        )
        channel.queue_bind(
            exchange=EXCHANGE_NAME_2, queue=QUEUE_NAME_EMAIL, routing_key="email"
        )

        contacts = Contact.objects()

        # sending messages to two different queues depending on the routing_key
        for contact in contacts:
            contact_id = contact.to_mongo().to_dict()["_id"]

            channel.basic_publish(
                exchange=EXCHANGE_NAME_2,
                routing_key=contact.send_to,  # "sms" or "email",
                body=str(contact_id).encode(),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ),
            )

            print("[x] Sent %r" % contact.to_mongo().to_dict())
    except AMQPConnectionError as err:
        print(f"RabbitMQ connection error: {err}")
        raise
    finally:
        if connection and connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
