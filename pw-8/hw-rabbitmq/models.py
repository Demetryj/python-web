from mongoengine import Document, BooleanField, StringField

from connection import (
    ROUTING_KEY_SMS,
    ROUTING_KEY_EMAIL,
)

class Contact(Document):
    fullname = StringField(required=True)
    address = StringField(max_length=120)
    email = StringField(max_length=100)
    phone = StringField(max_length=25)
    is_sent = BooleanField(default=False)
    send_to= StringField(choices=[ROUTING_KEY_SMS, ROUTING_KEY_EMAIL])
    meta = {"collection": "contacts"}