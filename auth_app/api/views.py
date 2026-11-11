"""API views for registration, authentication, and password recovery."""
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from auth_app.cookies import (clear_auth_cookies, set_auth_cookies, set_token_cookie)
from auth_app.utils import (decode_user, send_activation_email, send_password_reset_email)
from .serializers import (LoginSerializer, PasswordConfirmSerializer, PasswordResetSerializer, RegistrationSerializer)

User = get_user_model()

class RegisterView(APIView):
    """Create an inactive user and send an account activation email."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate registration data and return the created user."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = send_activation_email(user)
        return Response({
            "user": {"id": user.id, "email": user.email},
            "token": token
        }, status=status.HTTP_201_CREATED)


class ActivateView(APIView):
    """Activate a user account with an emailed one-time token."""
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """Validate the activation token and enable the user account."""
        user = decode_user(uidb64)
        if not user or not default_token_generator.check_token(user, token):
            return Response({"detail": "Activation failed."}, status=400)
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"message": "Account successfully activated."})


class LoginView(APIView):
    """Authenticate an active user and set HttpOnly JWT cookies."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate credentials and start a cookie-based session."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = RefreshToken.for_user(user)
        response = Response({
            "detail": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username
            }
        })
        set_auth_cookies(response, {
            "refresh": str(token),
            "access": str(token.access_token)
        })
        return response


class RefreshView(APIView):
    """Issue a new access token from the refresh-token cookie."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the refresh cookie and replace the access cookie."""
        token = request.COOKIES.get("refresh_token")
        if not token:
            return Response({"detail": "Refresh token is missing."}, status=400)
        try:
            access = str(RefreshToken(token).access_token)
        except TokenError:
            return Response({"detail": "Refresh token is invalid."}, status=401)
        response = Response({
            "detail": "Token refreshed",
            "access": access
        })
        set_token_cookie(response, "access_token", access)
        return response


class LogoutView(APIView):
    """Blacklist the refresh token and remove authentication cookies."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Invalidate the current refresh token and end the session."""
        token = request.COOKIES.get("refresh_token")
        if not token:
            return Response({"detail": "Refresh token is missing."}, status=400)
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            return Response({"detail": "Refresh token is invalid."}, status=401)
        response = Response({"detail": "Logout successful! All tokens were deleted."})
        clear_auth_cookies(response)
        return response


class PasswordResetView(APIView):
    """Send a password-reset email without exposing account existence."""
    permission_classes = [AllowAny]

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


class PasswordConfirmView(APIView):
    """Store a new password after validating a reset token."""
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """Validate token and password data before updating the user."""
        user = decode_user(uidb64)
        if not user or not default_token_generator.check_token(user, token):
            return Response({"detail": "Password reset failed."}, status=400)
        serializer = PasswordConfirmSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response({
            "detail": "Your Password has been successfully reset."
        })
