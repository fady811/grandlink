import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User Model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = None  # Remove username field

    objects = UserManager()
    role = models.CharField(
        max_length=20,
        choices=[
            ('student', 'Student'),
            ('employer', 'Employer'),
            ('admin', 'Admin'),
        ],
        default='student'
    )
    is_active = models.BooleanField(default=False)  # Requires email verification
    deletion_date = models.DateTimeField(null=True, blank=True)  # Soft delete

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return f"{self.email} ({self.role})"

    def soft_delete(self):
        """Mark account for deletion"""
        self.is_active = False
        self.deletion_date = timezone.now()
        self.save()

    def reactivate(self):
        """Reactivate within 30 days"""
        self.is_active = True
        self.deletion_date = None
        self.save()


class OTPVerification(models.Model):
    """OTP codes for email verification and password reset"""

    class Purpose(models.TextChoices):
        VERIFY_EMAIL = 'verify_email', 'Verify Email'
        RESET_PASSWORD = 'reset_password', 'Reset Password'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.VERIFY_EMAIL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # 10 min expiry
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    class Meta:
        indexes = [
            models.Index(fields=['user', 'expires_at']),
        ]
