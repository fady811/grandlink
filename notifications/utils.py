import logging
from .models import Notification
from .tasks import send_notification_email

logger = logging.getLogger(__name__)

def notify(user, type, message, related_object_id=None):
    """
    Create an in-app notification and trigger an async email notification.
    Ensures that failures in notification creation don't break the main flow.
    """
    try:
        # 1. Create In-App Notification
        notification = Notification.objects.create(
            user=user,
            type=type,
            message=message,
            related_object_id=related_object_id
        )

        # 2. Trigger Async Email Notification
        # Use a user-friendly title based on the type
        subject = f"GradLink: {notification.get_type_display()}"
        
        send_notification_email.delay(
            user_id=user.id,
            subject=subject,
            message=message
        )
        
        return notification

    except Exception as e:
        # Never raise exceptions from notify()
        logger.error(f"Error creating notification for user {user.id}: {str(e)}")
        return None
