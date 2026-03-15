import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class SupportTicket(models.Model):
    """
    Support ticket model to track user issues.
    """
    class Category(models.TextChoices):
        TECHNICAL = 'technical', 'Technical Issue'
        ACCOUNT = 'account', 'Account Issue'
        JOB_POSTING = 'job_posting', 'Job Posting'
        BILLING = 'billing', 'Billing'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        help_text='User who created the ticket'
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.TECHNICAL
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        help_text='Admin assigned to this ticket'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.status in [self.Status.RESOLVED, self.Status.CLOSED] and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status not in [self.Status.RESOLVED, self.Status.CLOSED]:
            self.resolved_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']


class TicketReply(models.Model):
    """
    Replies for a specific support ticket.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_replies'
    )
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.author.email} on Ticket #{self.ticket.id}"

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Ticket Replies'
