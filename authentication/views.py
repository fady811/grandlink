from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
from django.utils import timezone

from .models import User, OTPVerification
from .serializers import (
    UserRegisterSerializer, UserLoginSerializer,
    OTPVerificationSerializer, UserDetailSerializer,
)
from .utils import send_otp_email, send_password_reset_otp, verify_otp


# ═══════════════════════════════════════════════════════════════
#  REGISTRATION & VERIFICATION
# ═══════════════════════════════════════════════════════════════

class RegisterView(generics.CreateAPIView):
    """User registration (creates inactive user and sends OTP)"""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_otp_email(user)
        return Response({
            "message": "User created. Please verify your email with OTP.",
            "email": user.email
        }, status=status.HTTP_201_CREATED)


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        success, message = verify_otp(email, code, purpose=OTPVerification.Purpose.VERIFY_EMAIL)
        if success:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": message,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)
        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(generics.GenericAPIView):
    serializer_class = OTPVerificationSerializer  # reuse but we only need email
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({"error": "User already active."}, status=status.HTTP_400_BAD_REQUEST)
            send_otp_email(user)
            return Response({"message": "New OTP sent."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


# ═══════════════════════════════════════════════════════════════
#  LOGIN & OAUTH
# ═══════════════════════════════════════════════════════════════

class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, username=email, password=password)
        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserDetailSerializer(user).data
            })
        elif user and not user.is_active:
            return Response({"error": "Account not activated. Please verify email."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class GoogleAuthView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token')
        role = request.data.get('role')  # user selects role before Google login
        if not token or not role:
            return Response({"error": "Token and role required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify token
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
            email = idinfo['email']
            # Check if user exists
            user = User.objects.filter(email=email).first()
            if user:
                # Login existing user
                if not user.is_active:
                    # Activate because Google email is trusted
                    user.is_active = True
                    user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserDetailSerializer(user).data
                })
            else:
                # Create new user with role, auto-activate
                user = User.objects.create_user(
                    email=email,
                    role=role,
                    is_active=True
                )
                refresh = RefreshToken.for_user(user)
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserDetailSerializer(user).data
                })
        except ValueError:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════
#  PASSWORD RESET
# ═══════════════════════════════════════════════════════════════

class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /api/auth/password-reset/
    Sends a password-reset OTP to the given email address.
    Always returns 200 to avoid leaking whether the email is registered.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if email:
            try:
                user = User.objects.get(email=email, is_active=True)
                send_password_reset_otp(user)
            except User.DoesNotExist:
                pass  # Intentionally silent — do not reveal account existence
        return Response(
            {"message": "If this email is registered, a reset code has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /api/auth/password-reset/confirm/
    Verifies the OTP and sets the new password.
    Body: { email, code, new_password, new_password2 }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        code = request.data.get('code', '').strip()
        new_password = request.data.get('new_password', '')
        new_password2 = request.data.get('new_password2', '')

        if not all([email, code, new_password, new_password2]):
            return Response(
                {"error": "email, code, new_password, and new_password2 are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != new_password2:
            return Response(
                {"error": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify OTP first
        success, message = verify_otp(email, code, purpose=OTPVerification.Purpose.RESET_PASSWORD)
        if not success:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate password strength using Django's built-in validators
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response({"error": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password reset successfully. Please log in with your new password."},
            status=status.HTTP_200_OK,
        )


# ═══════════════════════════════════════════════════════════════
#  ACCOUNT MANAGEMENT (SOFT DELETE & REACTIVATION)
# ═══════════════════════════════════════════════════════════════

class SoftDeleteAccountView(generics.GenericAPIView):
    """
    DELETE /api/auth/account/
    Soft-deletes the authenticated user's account (marks inactive, sets deletion_date).
    Account can be reactivated within 30 days via /account/reactivate/.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.deletion_date:
            return Response(
                {"error": "Account is already scheduled for deletion."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.soft_delete()
        return Response(
            {"message": "Account scheduled for deletion. You may reactivate within 30 days."},
            status=status.HTTP_200_OK,
        )


class ReactivateAccountView(generics.GenericAPIView):
    """
    POST /api/auth/account/reactivate/
    Reactivates a soft-deleted account if within the 30-day window.
    Accepts email + password because the JWT bearer token won't work
    once is_active=False (DRF rejects inactive users on authentication).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {"error": "email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Bypass is_active check — look up user directly
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.deletion_date:
            return Response(
                {"error": "Account is not scheduled for deletion."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        days_since_deletion = (timezone.now() - user.deletion_date).days
        if days_since_deletion > 30:
            return Response(
                {"error": "Reactivation window has expired. Account cannot be recovered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.reactivate()
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Account reactivated successfully.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)