from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from .models import User, OTPVerification
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.verify_otp_url = reverse('verify-otp')
        self.login_url = reverse('login')
        self.token_refresh_url = reverse('token-refresh')
        self.password_reset_url = reverse('password-reset')
        self.password_reset_confirm_url = reverse('password-reset-confirm')
        self.account_url = reverse('soft-delete-account')
        self.reactivate_url = reverse('reactivate-account')

        # Data for API registration
        self.api_user_data = {
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'role': 'student',
        }
        # Data for direct model creation
        self.model_user_data = {
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!',
            'role': 'student',
        }

    def test_full_auth_flow(self):
        # 1. Register
        response = self.client.post(self.register_url, self.api_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.api_user_data['email']).exists())
        user = User.objects.get(email=self.api_user_data['email'])
        self.assertFalse(user.is_active)

        # 2. Verify OTP
        otp = OTPVerification.objects.filter(user=user, purpose=OTPVerification.Purpose.VERIFY_EMAIL).latest('created_at')
        verify_data = {
            'email': user.email,
            'code': otp.code
        }
        response = self.client.post(self.verify_otp_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # 3. Login
        login_data = {
            'email': self.api_user_data['email'],
            'password': self.api_user_data['password']
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data['refresh']

        # 4. Token Refresh
        refresh_data = {
            'refresh': refresh_token
        }
        response = self.client.post(self.token_refresh_url, refresh_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_password_reset_flow(self):
        # Setup active user
        user = User.objects.create_user(**self.model_user_data, is_active=True)

        # 1. Request Reset
        response = self.client.post(self.password_reset_url, {'email': user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(OTPVerification.objects.filter(user=user, purpose=OTPVerification.Purpose.RESET_PASSWORD).exists())

        # 2. Confirm Reset
        otp = OTPVerification.objects.filter(user=user, purpose=OTPVerification.Purpose.RESET_PASSWORD).latest('created_at')
        new_password = "NewStrongPassword456!"
        confirm_data = {
            'email': user.email,
            'code': otp.code,
            'new_password': new_password,
            'new_password2': new_password,
        }
        response = self.client.post(self.password_reset_confirm_url, confirm_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Verify login with new password
        login_data = {'email': user.email, 'password': new_password}
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_soft_delete_and_reactivation(self):
        # Setup active user
        user = User.objects.create_user(**self.model_user_data, is_active=True)
        self.client.force_authenticate(user=user)

        # 1. Soft Delete
        response = self.client.delete(self.account_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.deletion_date)

        # 2. Reactivate
        self.client.force_authenticate(user=None) # Logged out
        reactivate_data = {
            'email': user.email,
            'password': self.model_user_data['password']
        }
        response = self.client.post(self.reactivate_url, reactivate_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.deletion_date)
