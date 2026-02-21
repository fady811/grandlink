from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
from .models import User
from .serializers import UserRegisterSerializer, UserLoginSerializer, OTPVerificationSerializer, UserDetailSerializer
from .utils import send_otp_email, verify_otp

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

        success, message = verify_otp(email, code)
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