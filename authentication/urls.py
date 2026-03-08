from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import (
    RegisterView, VerifyOTPView, ResendOTPView, LoginView, GoogleAuthView,
    PasswordResetRequestView, PasswordResetConfirmView,
    SoftDeleteAccountView, ReactivateAccountView,
)

urlpatterns = [
    # ── Registration & Verification ──────────────────────────────
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),

    # ── Login & Token Management ─────────────────────────────────
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='logout'),

    # ── OAuth ────────────────────────────────────────────────────
    path('google/', GoogleAuthView.as_view(), name='google-auth'),

    # ── Password Reset ───────────────────────────────────────────
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # ── Account Management ───────────────────────────────────────
    path('account/', SoftDeleteAccountView.as_view(), name='soft-delete-account'),
    path('account/reactivate/', ReactivateAccountView.as_view(), name='reactivate-account'),
]