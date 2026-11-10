"""JWT authentication using tokens stored in HttpOnly cookies."""

from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate requests with the access token cookie."""

    def authenticate(self, request):
        """Return the authenticated user for a valid access cookie."""
        access_token = request.COOKIES.get("access_token")
        if not access_token:
            return None
        validated_token = self.get_validated_token(access_token)
        return self.get_user(validated_token), validated_token
