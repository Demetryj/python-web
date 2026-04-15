from django.db import models


class Author(models.Model):
    fullname = models.CharField(max_length=255, null=False, unique=True)
    born_date = models.CharField(max_length=50)
    born_location = models.CharField(max_length=300)
    description = models.TextField()

    def __str__(self):
        return f"{self.fullname}"


class Tag(models.Model):
    name = models.CharField(max_length=35, unique=True)

    def __str__(self):
        return self.name


class Quote(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="quotes")
    tags = models.ManyToManyField(Tag, blank=True, related_name="quotes")
    quote = models.TextField(unique=True)

    def __str__(self):
        return self.quote[:60]


# Because of the ManyToManyField between Quote and Tag, Django automatically
# creates the intermediate join table `quotes_app_quote_tags` after migrations
# (id, quote_id, tag_id).
# This table allows one quote to have many tags, and one tag to belong to many quotes.
#
# `related_name="quotes"` provides reverse access:
# - for Author: `author.quotes.all()` (instead of `author.quote_set.all()`)
# - for Tag: `tag.quotes.all()` (instead of `tag.quote_set.all()`)
