"""Helpers for creating and removing JWT authentication cookies."""

from django.conf import settings


def set_token_cookie(response, key, token):
    """Attach one secure HttpOnly token cookie to a response."""
    response.set_cookie(
        key=key,
        value=token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=settings.AUTH_COOKIE_MAX_AGES[key],
        path="/",
    )


def set_auth_cookies(response, tokens):
    """Attach available access and refresh tokens to a response."""
    set_token_cookie(response, "access_token", tokens["access"])
    if tokens.get("refresh"):
        set_token_cookie(response, "refresh_token", tokens["refresh"])


def clear_auth_cookies(response):
    """Remove access and refresh token cookies from a response."""
    options = {"samesite": settings.AUTH_COOKIE_SAMESITE, "path": "/"}
    response.delete_cookie("access_token", **options)
    response.delete_cookie("refresh_token", **options)
