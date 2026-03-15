import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .models import OTPVerification, User
from datetime import timedelta
from django.utils import timezone

from configuration.utils import get_setting

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_otp_email(user):
    """Create OTP and send stylized HTML email (email verification)"""
    otp_code = generate_otp()
    expiry_minutes = get_setting('otp_expire_minutes')
    
    # Remove previous unused OTPs for this user + purpose
    OTPVerification.objects.filter(
        user=user, purpose=OTPVerification.Purpose.VERIFY_EMAIL
    ).delete()
    OTPVerification.objects.create(
        user=user,
        code=otp_code,
        purpose=OTPVerification.Purpose.VERIFY_EMAIL,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )

    context = {
        'user': user,
        'otp_code': otp_code,
        'expiry_minutes': expiry_minutes,
    }

    html_message = render_to_string('emails/otp_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        'Your GradLink Verification Code',
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def send_password_reset_otp(user):
    """Create OTP and send password reset email"""
    otp_code = generate_otp()
    expiry_minutes = get_setting('otp_expire_minutes')
    
    # Remove previous reset OTPs for this user
    OTPVerification.objects.filter(
        user=user, purpose=OTPVerification.Purpose.RESET_PASSWORD
    ).delete()
    OTPVerification.objects.create(
        user=user,
        code=otp_code,
        purpose=OTPVerification.Purpose.RESET_PASSWORD,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )

    context = {
        'user': user,
        'otp_code': otp_code,
        'expiry_minutes': expiry_minutes,
        'purpose': 'password reset',
    }

    html_message = render_to_string('emails/otp_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        'Your GradLink Password Reset Code',
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def verify_otp(email, code, purpose=OTPVerification.Purpose.VERIFY_EMAIL):
    """Validate OTP for a given purpose. Activates user on email-verification success."""
    max_attempts = get_setting('otp_max_attempts')
    
    try:
        user = User.objects.get(email=email)
        otp = OTPVerification.objects.filter(
            user=user, is_used=False, purpose=purpose
        ).latest('created_at')
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        return False, "Invalid email or code."

    if otp.attempt_count >= max_attempts:
        return False, "Maximum attempts exceeded. Request a new code."

    otp.attempt_count += 1
    otp.save()

    if not otp.is_valid():
        return False, "Code expired. Request a new one."

    if otp.code != code:
        return False, "Invalid code."

    # Success — clean up OTP
    otp.delete()

    # Only activate user on email-verification purpose
    if purpose == OTPVerification.Purpose.VERIFY_EMAIL:
        user.is_active = True
        user.save()

    return True, "Verified successfully."
