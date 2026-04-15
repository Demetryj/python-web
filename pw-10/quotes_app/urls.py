from django.urls import path
from . import views

app_name = "quotes_app"

urlpatterns = [
    path("", views.main, name="main"),
    path("author/<int:author_id>/", views.about_author, name="author"),
    path("add-author/", views.add_author, name="add_author"),
    path("add-quote/", views.add_quote, name="add_quote"),
]
