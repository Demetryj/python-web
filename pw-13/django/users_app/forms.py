"""Authentication-related forms for the users_app.

Contains:
- RegisterForm for creating a new user account
- LoginForm for authenticating an existing user
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    username = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control auth-input"}),
    )

    email = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control auth-input"}),
    )

    password1 = forms.CharField(
        min_length=6,
        max_length=20,
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control auth-input"}),
    )
    password2 = forms.CharField(
        min_length=6,
        max_length=20,
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control auth-input"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control auth-input"}),
    )

    password = forms.CharField(
        min_length=6,
        max_length=20,
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control auth-input"}),
    )

    class Meta:
        model = User
        fields = ["username", "password"]
