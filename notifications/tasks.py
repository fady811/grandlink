from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task(name='notifications.tasks.send_notification_email')
def send_notification_email(user_id, subject, message):
    """
    Send an async styled HTML email notification.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return f"User {user_id} not found."

    context = {
        'user': user,
        'subject': subject,
        'message': message,
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8080'),
    }

    html_content = render_to_string('emails/notification_email.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

@shared_task(name='notifications.tasks.send_bulk_announcement')
def send_bulk_announcement(user_ids, subject, message):
    """
    Send bulk announcements: creates in-app notifications and sends emails.
    """
    from notifications.utils import notify
    from notifications.models import Notification

    users = User.objects.filter(id__in=user_ids)
    
    for user in users:
        # 1. Create In-App Notification (this also triggers individual email via notify() if we want)
        # However, for HUGE bulks, we might want to optimize.
        # But notify() is already async for email, so it's fine.
        notify(
            user=user,
            type=Notification.NotificationType.ANNOUNCEMENT,
            message=message
        )
    
    return f"Bulk announcement initiated for {len(user_ids)} users."
