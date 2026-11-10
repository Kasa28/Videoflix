"""Tests for account activation and password reset."""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class ActivationTests(APITestCase):
    """Verify activation and password reset token flows."""

    def setUp(self):
        """Create one inactive user and its encoded ID."""
        self.user = User.objects.create_user(
            username="user@example.com", email="user@example.com",
            password="StrongPass123!", is_active=False,
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))

    def test_activation_enables_user(self):
        """A valid activation token enables the account."""
        token = default_token_generator.make_token(self.user)
        response = self.client.get(f"/api/activate/{self.uid}/{token}/")
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_active)

    def test_password_confirmation_changes_password(self):
        """A valid reset token stores the new hashed password."""
        token = default_token_generator.make_token(self.user)
        payload = {"new_password": "NewStrongPass456!", "confirm_password": "NewStrongPass456!"}
        response = self.client.post(
            f"/api/password_confirm/{self.uid}/{token}/", payload, format="json"
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(payload["new_password"]))
