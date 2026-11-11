"""API views for registration, authentication, and password recovery."""
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from auth_app.cookies import (clear_auth_cookies, set_auth_cookies, set_token_cookie)
from auth_app.utils import (decode_user, send_activation_email, send_password_reset_email)
from .serializers import (LoginSerializer, PasswordConfirmSerializer, PasswordResetSerializer, RegistrationSerializer)

User = get_user_model()


class PublicAPIView(APIView):
    """Allow public access without evaluating a stale access-token cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]


class RegisterView(PublicAPIView):
    """Create an inactive user and send an account activation email."""

    def post(self, request):
        """Validate registration data and return the created user."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_activation_email(user)
        data = {"user": 
                {"id": user.id,
                "email": user.email}}
        return Response(data, status=status.HTTP_201_CREATED)


class ActivateView(PublicAPIView):
    """Activate a user account with an emailed one-time token."""

    def get(self, request, uidb64, token):
        """Validate the activation token and enable the user account."""
        user = decode_user(uidb64)
        if not user or not default_token_generator.check_token(user, token):
            return error_response("Activation failed.", status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"message": "Account successfully activated."})


class LoginView(PublicAPIView):
    """Authenticate an active user and set HttpOnly JWT cookies."""

    def post(self, request):
        """Validate credentials and start a cookie-based session."""
        serializer = LoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as error:
            return error_response(str(error.detail), status.HTTP_401_UNAUTHORIZED)
        user = serializer.validated_data["user"]
        return create_login_response(user)


class RefreshView(PublicAPIView):
    """Issue a new access token from the refresh-token cookie."""

    def post(self, request):
        """Validate the refresh cookie and replace the access cookie."""
        token = request.COOKIES.get("refresh_token")
        if not token:
            return error_response(
                "Refresh token is missing.", status.HTTP_400_BAD_REQUEST
            )
        try:
            access = str(RefreshToken(token).access_token)
        except TokenError:
            return error_response(
                "Refresh token is invalid.", status.HTTP_401_UNAUTHORIZED
            )
        response = Response({"detail": "Token refreshed", "access": access})
        set_token_cookie(response, "access_token", access)
        return response


class LogoutView(PublicAPIView):
    """Blacklist the refresh token and remove authentication cookies."""

    def post(self, request):
        """Invalidate the current refresh token and end the session."""
        token = request.COOKIES.get("refresh_token")
        if not token:
            return error_response(
                "Refresh token is missing.", status.HTTP_400_BAD_REQUEST
            )
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            return error_response(
                "Refresh token is invalid.", status.HTTP_401_UNAUTHORIZED
            )
        response = Response({"detail": "Logout successful! All tokens were deleted."})
        clear_auth_cookies(response)
        return response


class PasswordResetView(PublicAPIView):
    """Send a password-reset email without exposing account existence."""

    def post(self, request):
        """Validate the email and send a reset link when a user exists."""
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()
        if user:
            send_password_reset_email(user)
        return Response({
            "detail": "An email has been sent to reset your password."
        })


class PasswordConfirmView(PublicAPIView):
    """Store a new password after validating a reset token."""

    def post(self, request, uidb64, token):
        """Validate token and password data before updating the user."""
        user = decode_user(uidb64)
        if not user or not default_token_generator.check_token(user, token):
            return error_response(
                "Password reset failed.", status.HTTP_400_BAD_REQUEST
            )
        serializer = PasswordConfirmSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Your Password has been successfully reset."})


def create_login_response(user):
    """Build a successful login response and attach both JWT cookies."""
    refresh = RefreshToken.for_user(user)
    data = {
        "detail": "Login successful",
        "user": {"id": user.id, "username": user.username},
    }
    response = Response(data)
    set_auth_cookies(response, token_data(refresh))
    return response


def token_data(refresh):
    """Return string representations of a refresh and access token pair."""
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


def error_response(message, status_code):
    """Return a consistent detail response with a DRF status constant."""
    return Response({"detail": message}, status=status_code)
