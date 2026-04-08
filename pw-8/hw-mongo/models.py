from mongoengine import CASCADE, Document, ListField, ReferenceField, StringField


class Author(Document):
    fullname = StringField(required=True, unique=True)
    born_date = StringField(max_length=50)
    born_location = StringField(max_length=150)
    description = StringField()
    meta = {"collection": "authors"}


class Quote(Document):
    author = ReferenceField(Author, required=True, reverse_delete_rule=CASCADE)
    tags = ListField(StringField(max_length=20))
    quote = StringField(required=True)
    meta = {"collection": "quotes"}
