import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .models import OTPVerification, User
from datetime import timedelta
from django.utils import timezone

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_otp_email(user):
    """Create OTP and send stylized HTML email"""
    otp_code = generate_otp()
    # Invalidate previous unused OTPs for this user
    OTPVerification.objects.filter(user=user, is_used=False).update(is_used=True)
    otp = OTPVerification.objects.create(
        user=user,
        code=otp_code,
        expires_at=timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    )
    
    # Context for the template
    context = {
        'user': user,
        'otp_code': otp_code,
        'expiry_minutes': settings.OTP_EXPIRE_MINUTES,
    }
    
    # Render HTML and create plain text version
    html_message = render_to_string('emails/otp_email.html', context)
    plain_message = strip_tags(html_message)
    
    subject = 'Your GradLink Verification Code'
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message
    )
    return otp

def verify_otp(email, code):
    """Validate OTP and activate user if correct"""
    try:
        user = User.objects.get(email=email)
        otp = OTPVerification.objects.filter(user=user, is_used=False).latest('created_at')
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        return False, "Invalid email or code."

    if otp.attempt_count >= settings.OTP_MAX_ATTEMPTS:
        return False, "Maximum attempts exceeded. Request a new code."

    otp.attempt_count += 1
    otp.save()

    if not otp.is_valid():
        return False, "Code expired. Request a new one."

    if otp.code != code:
        return False, "Invalid code."

    # Success
    otp.is_used = True
    otp.save()
    user.is_active = True
    user.save()
    return True, "Email verified successfully."