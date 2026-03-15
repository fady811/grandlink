import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    Platform-wide notification system.
    """

    class NotificationType(models.TextChoices):
        APPLICATION_RECEIVED = 'application_received', 'Application Received'
        APPLICATION_STATUS_CHANGED = 'application_status_changed', 'Application Status Changed'
        INTERVIEW_SCHEDULED = 'interview_scheduled', 'Interview Scheduled'
        INTERVIEW_CONFIRMED = 'interview_confirmed', 'Interview Confirmed'
        INTERVIEW_CANCELLED = 'interview_cancelled', 'Interview Cancelled'
        JOB_APPROVED = 'job_approved', 'Job Approved'
        JOB_REJECTED = 'job_rejected', 'Job Rejected'
        ANNOUNCEMENT = 'announcement', 'Announcement'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )

    # ── Content ─────────────────────────────────────────────────
    type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
    )
    message = models.TextField()

    # ── Optional reference to the related object ────────────────
    related_object_id = models.UUIDField(null=True, blank=True)

    # ── State ───────────────────────────────────────────────────
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} → {self.user.email}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
