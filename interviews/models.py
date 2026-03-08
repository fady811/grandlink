import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Interview(models.Model):
    """
    An interview session scheduled by an employer for a specific application.
    Multiple interviews can exist per application (e.g. Round 1, Round 2).
    """

    class InterviewType(models.TextChoices):
        IN_PERSON = 'in_person', 'In Person'
        VIDEO = 'video', 'Video Call'
        PHONE = 'phone', 'Phone Call'

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        'jobs.Application',
        on_delete=models.CASCADE,
        related_name='interviews',
    )
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_interviews',
        help_text='Employer who created this interview',
    )

    # ── Interview Details ────────────────────────────────────────
    title = models.CharField(
        max_length=255,
        help_text='e.g. "Technical Round 1", "HR Screening"',
    )
    description = models.TextField(
        blank=True,
        help_text='Agenda, preparation instructions, dress code, etc.',
    )
    interview_type = models.CharField(
        max_length=20,
        choices=InterviewType.choices,
        default=InterviewType.VIDEO,
    )

    # ── Scheduling ───────────────────────────────────────────────
    scheduled_at = models.DateTimeField(
        help_text='Date and time the interview starts',
    )
    duration_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(480)],
        help_text='Duration in minutes (15–480)',
    )

    # ── Location / Link ──────────────────────────────────────────
    location = models.CharField(
        max_length=500,
        blank=True,
        help_text='Physical address for in-person interviews',
    )
    meeting_link = models.URLField(
        blank=True,
        help_text='Zoom / Teams / Google Meet link for video interviews',
    )

    # ── Status ───────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    cancellation_reason = models.TextField(
        blank=True,
        help_text='Reason for cancellation (filled when status=cancelled)',
    )

    # ── Timestamps ───────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} — {self.application.student.user.email} ({self.get_status_display()})"

    @property
    def job(self):
        return self.application.job

    @property
    def student(self):
        return self.application.student

    @property
    def employer_profile(self):
        return self.application.job.employer

    class Meta:
        ordering = ['scheduled_at']
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'
        indexes = [
            models.Index(fields=['application', 'status']),
            models.Index(fields=['scheduled_by', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['status', 'scheduled_at']),
        ]


class InterviewFeedback(models.Model):
    """
    Post-interview evaluation submitted by the employer.
    One feedback record per interview.
    """

    class Recommendation(models.TextChoices):
        STRONG_YES = 'strong_yes', 'Strong Yes'
        YES = 'yes', 'Yes'
        MAYBE = 'maybe', 'Maybe'
        NO = 'no', 'No'
        STRONG_NO = 'strong_no', 'Strong No'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview = models.OneToOneField(
        Interview,
        on_delete=models.CASCADE,
        related_name='feedback',
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_feedbacks',
    )

    # ── Ratings (1–5) ────────────────────────────────────────────
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Overall rating (1–5)',
    )
    technical_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Technical skills rating (1–5)',
    )
    communication_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Communication rating (1–5)',
    )
    cultural_fit_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Cultural fit rating (1–5)',
    )

    # ── Written Feedback ─────────────────────────────────────────
    strengths = models.TextField(blank=True, help_text='Candidate strengths')
    weaknesses = models.TextField(blank=True, help_text='Areas for improvement')
    notes = models.TextField(blank=True, help_text='General notes')

    # ── Recommendation ───────────────────────────────────────────
    recommendation = models.CharField(
        max_length=20,
        choices=Recommendation.choices,
        help_text='Overall hiring recommendation',
    )

    # ── Timestamps ───────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.interview.title} — {self.get_recommendation_display()}"

    class Meta:
        verbose_name = 'Interview Feedback'
        verbose_name_plural = 'Interview Feedbacks'
