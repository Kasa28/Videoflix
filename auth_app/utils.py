"""Utilities for account activation and password reset emails."""
from email import encoders
from email.mime.base import MIMEBase
from pathlib import Path
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()
LOGO_PATH = Path(__file__).parent / "templates" / "auth_app" / "emails" / "logo.png"


def encode_user_id(user):
    """Return the URL-safe representation of a user ID."""
    return urlsafe_base64_encode(force_bytes(user.pk))


def decode_user(uidb64):
    """Resolve a URL-safe user ID or return None."""
    try:
        return User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def build_frontend_link(page, user, token):
    """Build a frontend URL containing uid and token query parameters."""
    query = urlencode({"uid": encode_user_id(user), "token": token})
    return f"{settings.FRONTEND_URL}/pages/auth/{page}?{query}"


def send_account_email(user, subject, page, template_name):
    """Render and send one authentication email."""
    token = default_token_generator.make_token(user)
    context = {"user": user, "action_url": build_frontend_link(page, user, token)}
    text = render_to_string(f"auth_app/emails/{template_name}.txt", context)
    html = render_to_string(f"auth_app/emails/{template_name}.html", context)
    email = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.attach_alternative(html, "text/html")
    attach_logo(email)
    email.send()


def attach_logo(email):
    """Attach the supplied Videoflix logo as an inline related image."""
    logo = MIMEBase("image", "png")
    logo.set_payload(LOGO_PATH.read_bytes())
    encoders.encode_base64(logo)
    logo.add_header("Content-ID", "<videoflix-logo>")
    logo.add_header("Content-Disposition", "inline", filename="logo.png")
    email.attach(logo)


def send_activation_email(user):
    """Send the account activation email."""
    send_account_email(
        user, "Confirm your email", "activate.html", "activation"
    )


def send_password_reset_email(user):
    """Send the password reset email."""
    send_account_email(
        user, "Reset your Password", "confirm_password.html", "password_reset"
    )
