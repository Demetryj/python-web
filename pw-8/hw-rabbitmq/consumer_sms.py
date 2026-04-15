import os
import sys

from connection import init_mongoDB, init_rabbitMQ, QUEUE_NAME_SMS
from models import Contact


def update_contact(contact: Contact) -> None:
    # Mark the contact as processed and persist the change.
    contact.is_sent = True
    contact.save()


def send_email(contact_email: str) -> None:
    print(f"Email sent {contact_email}")


def callback_handler(ch, method, properties, body):
    # RabbitMQ message body contains contact id from producer.
    contact_id = body.decode()
    print(f" [x] Received {contact_id}")

    # Find the contact by id in MongoDB.
    contact = Contact.objects(id=contact_id).first()
    if contact is None:
        # Acknowledge unknown ids to avoid endless redelivery loop.
        print(f" [!] Contact not found for id={contact_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Simulate email sending and update delivery status.
    update_contact(contact)
    send_email(contact.email)

    # Confirm successful message processing.
    print(f" [x] Done: {method.delivery_tag}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = None

    init_mongoDB()
    try:
        # Connect to RabbitMQ and declare queue used by producer.
        connection = init_rabbitMQ()
        if connection is None:
            raise RuntimeError("RabbitMQ connection is not available.")

        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME_SMS, durable=True)
        print(" [*] Waiting for messages. To exit press CTRL+C")

        # Process one message at a time per consumer instance.
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=QUEUE_NAME_SMS, on_message_callback=callback_handler
        )
        channel.start_consuming()
    finally:
        if connection and connection.is_open:
            connection.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
