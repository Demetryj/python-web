"""Form classes for creating and validating Author and Quote records.

Contains:
- AuthorForm for author profile data input
- QuoteForm for quote text, author selection, and tag selection
"""

from django.forms import (
    ModelChoiceField,
    ModelForm,
    CharField,
    ModelMultipleChoiceField,
    Select,
    SelectMultiple,
    TextInput,
    Textarea,
)
from .models import Author, Quote, Tag


class AuthorForm(ModelForm):
    fullname = CharField(
        min_length=3,
        max_length=255,
        required=True,
        widget=TextInput(attrs={"class": "form-control"}),
    )
    born_date = CharField(
        min_length=10,
        max_length=50,
        required=True,
        widget=TextInput(attrs={"class": "form-control"}),
    )
    born_location = CharField(
        min_length=10,
        max_length=300,
        required=True,
        widget=TextInput(attrs={"class": "form-control"}),
    )
    description = CharField(
        min_length=10, required=True, widget=Textarea(attrs={"class": "form-control"})
    )

    class Meta:
        model = Author
        fields = ["fullname", "born_date", "born_location", "description"]


class QuoteForm(ModelForm):
    quote = CharField(
        min_length=10, required=True, widget=Textarea(attrs={"class": "form-control"})
    )
    author = ModelChoiceField(
        queryset=Author.objects.all(),
        widget=Select(attrs={"class": "form-select"}),
    )
    tags = ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=SelectMultiple(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Quote
        fields = ["quote", "author", "tags"]
