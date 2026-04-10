from mongoengine import Document, BooleanField, StringField

class Contact(Document):
    fullname = StringField(required=True)
    address = StringField(max_length=120)
    email = StringField(max_length=100)
    phone = StringField(max_length=25)
    is_sent = BooleanField(default=False)
    meta = {"collection": "contacts"}