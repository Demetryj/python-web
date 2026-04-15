""" URL routes for the quotes_app.
 This file maps HTTP paths to view functions:
 - main page with quotes list
 - author details page
 - add author page
 - add quote page
 """

from django.urls import path
from . import views

app_name = "quotes_app"

urlpatterns = [
    path("", views.main, name="main"),
    path("author/<int:author_id>/", views.about_author, name="author"),
    path("add-author/", views.add_author, name="add_author"),
    path("add-quote/", views.add_quote, name="add_quote"),
    path("quotes_by_tag/<int:tag_id>/", views.show_quotes_by_tag, name="quotes_by_tag"),
]
