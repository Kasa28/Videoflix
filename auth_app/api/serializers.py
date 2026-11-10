"""Serializers for Videoflix authentication requests."""

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed


User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and create a Django user."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        """Configure fields exposed during registration."""
        model = User
        fields = ("email", "password", "confirmed_password")

    def validate(self, data):
        """Reject invalid registration data with a generic message."""
        duplicate = User.objects.filter(email__iexact=data["email"]).exists()
        mismatch = data["password"] != data["confirmed_password"]
        if duplicate or mismatch:
            message = "Please check your input and try again."
            raise serializers.ValidationError(message)
        return data

    def create(self, validated_data):
        """Create an inactive user whose internal username is the email."""
        validated_data.pop("confirmed_password")
        email = User.objects.normalize_email(validated_data.pop("email"))
        return User.objects.create_user(
            username=email, email=email, is_active=False, **validated_data
        )


class LoginSerializer(serializers.Serializer):
    """Authenticate an active user using email and password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Return the user without revealing why authentication failed."""
        email = User.objects.normalize_email(attrs["email"])
        user = authenticate(username=email, password=attrs["password"])
        if user is None:
            raise AuthenticationFailed("Email or password is incorrect.")
        attrs["user"] = user
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Validate a password-reset email request."""

    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):
    """Validate both fields of a new password request."""

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Require matching passwords and apply Django validation."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(attrs["new_password"], self.context.get("user"))
        return attrs
