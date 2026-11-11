"""Tests for user registration."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class RegistrationTests(APITestCase):
    """Verify registration validation and user creation."""

    def setUp(self):
        """Create an existing user for duplicate-data tests."""
        self.user = User.objects.create_user(
            username="quizzer",
            email="quizzer@example.com",
            password="StrongPass123!",
        )

    def test_registration_creates_user_with_hashed_password(self):
        """Registration creates a usable account without exposing passwords."""
        payload = {
            "email": "new@example.com",
            "password": "StrongPass456!", "confirmed_password": "StrongPass456!",
        }
        response = self.client.post("/api/register/", payload, format="json")
        user = User.objects.get(email="new@example.com")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertEqual(user.username, user.email)
        self.assertFalse(user.is_active)
        self.assertNotIn("password", response.data)

    def test_registration_rejects_duplicate_email(self):
        """Email addresses cannot be registered twice, regardless of case."""
        payload = {
            "email": "QUIZZER@example.com",
            "password": "StrongPass456!", "confirmed_password": "StrongPass456!",
        }
        response = self.client.post("/api/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_registration_ignores_stale_access_cookie(self):
        """A stale session cookie cannot block the public registration view."""
        self.client.cookies["access_token"] = "expired-token"
        payload = {
            "email": "stale-cookie@example.com",
            "password": "StrongPass456!",
            "confirmed_password": "StrongPass456!",
        }
        response = self.client.post("/api/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
