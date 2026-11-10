"""Tests for refreshing and revoking JWT cookies."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


User = get_user_model()


class TokenTests(APITestCase):
    """Test token refresh, logout and blacklisting."""

    def setUp(self):
        """Create a user and reusable login credentials."""
        self.credentials = {"email": "quizer@gmail.com", "password": "QuizerPass123!"}
        self.user = User.objects.create_user(
            username=self.credentials["email"], **self.credentials
        )

    def test_refresh_uses_refresh_cookie(self):
        """A valid refresh cookie creates a new access cookie."""
        self.client.post("/api/login/", self.credentials, format="json")
        response = self.client.post("/api/token/refresh/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)

    def test_refresh_without_cookie(self):
        """Refresh fails when no refresh cookie exists."""
        response = self.client.post("/api/token/refresh/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_with_invalid_token(self):
        """Refresh fails when the token is invalid."""
        self.client.cookies["refresh_token"] = "invalid_token"
        response = self.client.post("/api/token/refresh/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_and_deletes_cookies(self):
        """Logout blacklists the refresh token and deletes both cookies."""
        self.client.post("/api/login/", self.credentials, format="json")
        response = self.client.post("/api/logout/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BlacklistedToken.objects.count(), 1)
        self.assertEqual(response.cookies["access_token"]["max-age"], 0)
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)

    def test_logout_only_requires_refresh_cookie(self):
        """Logout still works after the access cookie is unavailable."""
        self.client.post("/api/login/", self.credentials, format="json")
        del self.client.cookies["access_token"]
        response = self.client.post("/api/logout/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blacklisted_token_cannot_be_refreshed(self):
        """A blacklisted refresh token cannot create new access tokens."""
        self.client.post("/api/login/", self.credentials, format="json")
        old_refresh = self.client.cookies["refresh_token"].value
        self.client.post("/api/logout/", {}, format="json")
        self.client.cookies["refresh_token"] = old_refresh
        response = self.client.post("/api/token/refresh/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
