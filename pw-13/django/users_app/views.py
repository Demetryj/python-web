"""Views for authentication flows in users_app.

Includes handlers for:
- user registration
- user login
- user logout
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from .forms import RegisterForm, LoginForm


def signup_user(request):
    """Handle user registration and render the sign-up page."""
    if request.user.is_authenticated:
        return redirect(to='quotes_app:main')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(to='users_app:login')
        else:
            return render(request, 'users_app/signup.html', context={"form": form})

    return render(request, 'users_app/signup.html', context={"form": RegisterForm()})


def login_user(request):
    """Authenticate user credentials and render the login page."""
    if request.user.is_authenticated:
        return redirect(to='quotes_app:main')

    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is None:
            messages.error(request, 'Username or password didn\'t match')
            return redirect(to='users_app:login')

        login(request, user)
        return redirect(to='quotes_app:main')

    return render(request, 'users_app/login.html', context={"form": LoginForm()})


@login_required
def logout_user(request):
    """Log out the current user and redirect to the main page."""
    logout(request)
    return redirect(to='quotes_app:main')


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    """Render password reset form and send reset instructions by email."""

    # Page with the email input form for starting password reset.
    template_name: str = 'users_app/password_reset.html'

    # Plain-text email template used by Django's password reset email sender.
    email_template_name: str = 'users_app/password_reset_email.html'

    # HTML email template for clients that support rich email content.
    html_email_template_name: str = 'users_app/password_reset_email.html'

    # Redirect target after Django successfully creates and sends the reset email.
    success_url = reverse_lazy('users_app:password_reset_done')

    # Message shown after submitting the reset form successfully.
    success_message: str = (
        "An email with instructions to reset your password has been sent to %(email)s."
    )

    # Subject template for the password reset email.
    subject_template_name: str = 'users_app/password_reset_subject.txt'
