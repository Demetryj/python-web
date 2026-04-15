from django.urls import path
from . import views

app_name = "quotes_app"

urlpatterns = [
    path("", views.main, name="main"),
]
