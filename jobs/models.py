import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Skill(models.Model):
    """
    Normalized skills table — shared between Jobs & Students.
    Example: Python, Django, Communication, etc.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    category = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('technical', 'Technical'),
            ('soft', 'Soft Skill'),
            ('language', 'Language'),
            ('tool', 'Tool/Software'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'


from django.utils.text import slugify


class JobCategory(models.Model):
    """Classification for jobs (e.g. Engineering, Marketing, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Job Category'
        verbose_name_plural = 'Job Categories'
        ordering = ['name']


class Job(models.Model):
    """Job posting by an Employer."""

    class WorkType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full Time'
        PART_TIME = 'part_time', 'Part Time'
        INTERNSHIP = 'internship', 'Internship'
        CONTRACT = 'contract', 'Contract'
        REMOTE = 'remote', 'Remote'

    class ExperienceLevel(models.TextChoices):
        ENTRY = 'entry', 'Entry Level'
        MID = 'mid', 'Mid Level'
        SENIOR = 'senior', 'Senior Level'
        FRESH_GRAD = 'fresh_grad', 'Fresh Graduate'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        CLOSED = 'closed', 'Closed'
        EXPIRED = 'expired', 'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(
        'profiles.EmployerProfile',
        on_delete=models.CASCADE,
        related_name='jobs',
    )
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs',
    )

    # ── Job Details ──────────────────────────────────────────────
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    requirements = models.TextField(blank=True, help_text='What is required from the applicant')
    responsibilities = models.TextField(blank=True, help_text='Job responsibilities')

    # ── Classification ───────────────────────────────────────────
    work_type = models.CharField(
        max_length=20,
        choices=WorkType.choices,
        default=WorkType.FULL_TIME,
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.ENTRY,
    )
    skills = models.ManyToManyField(Skill, blank=True, related_name='jobs')

    # ── Location ─────────────────────────────────────────────────
    location = models.CharField(max_length=255, blank=True)
    is_remote = models.BooleanField(default=False)

    # ── Compensation ─────────────────────────────────────────────
    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    hide_salary = models.BooleanField(default=False)

    # ── Status & Dates ───────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(
        default=False,
        help_text='Featured jobs appear at the top of the search results.'
    )

    # ── Analytics ────────────────────────────────────────────────
    views_count = models.PositiveIntegerField(default=0)

    # ── Review / Approval / Moderation ───────────────────────────
    is_flagged = models.BooleanField(
        default=False,
        help_text='Automatically set to True if the job receives 5+ reports. Hides the job from public listings.',
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection (filled by admin when rejecting a job)',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_jobs',
        help_text='Admin who approved or rejected this job',
    )
    reviewed_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When the job was approved or rejected',
    )
    submitted_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When the employer submitted the job for review',
    )

    def __str__(self):
        return f"{self.title} — {self.employer.company_name}"

    @property
    def is_expired(self):
        if self.deadline and self.deadline < timezone.now():
            return True
        return self.status == self.Status.EXPIRED

    @property
    def applications_count(self):
        return self.applications.count()

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.salary_min and self.salary_max:
            if self.salary_min > self.salary_max:
                raise ValidationError(
                    {'salary_min': 'Minimum salary cannot exceed maximum salary.'}
                )
        
        # Enforce max_active_jobs limit from subscription
        if self.status == self.Status.ACTIVE:
            from billing.models import EmployerSubscription
            max_jobs = 3  # Default for free tier
            
            try:
                # Use getattr to safely check for the one-to-one relationship
                subscription = getattr(self.employer, 'subscription', None)
                if subscription and subscription.is_valid and subscription.plan:
                    max_jobs = subscription.plan.max_active_jobs
            except Exception:
                pass
            
            active_count = Job.objects.filter(
                employer=self.employer, 
                status=self.Status.ACTIVE
            ).exclude(id=self.id).count()
            
            if active_count >= max_jobs:
                raise ValidationError(
                    f"You have reached the maximum number of active jobs ({max_jobs}) allowed for your current plan."
                )

    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        indexes = [
            models.Index(fields=['status', 'deadline']),
            models.Index(fields=['work_type']),
            models.Index(fields=['experience_level']),
            models.Index(fields=['employer', 'status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['location']),
        ]


class Application(models.Model):
    """Student application for a Job."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        REVIEWING = 'reviewing', 'Under Review'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        INTERVIEW = 'interview', 'Interview Scheduled'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    student = models.ForeignKey(
        'profiles.StudentProfile',
        on_delete=models.CASCADE,
        related_name='applications',
    )

    # ── Application Content ──────────────────────────────────────
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='applications/resumes/', null=True, blank=True)

    # ── Status Tracking ──────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    employer_notes = models.TextField(blank=True, help_text='Private notes by the employer')

    # ── Dates ────────────────────────────────────────────────────
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.email} → {self.job.title}"

    class Meta:
        ordering = ['-applied_at']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'student'],
                name='unique_application_per_job',
            )
        ]
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['-applied_at']),
        ]


class SavedJob(models.Model):
    """Bookmarked / Saved Jobs by Students."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'profiles.StudentProfile',
        on_delete=models.CASCADE,
        related_name='saved_jobs',
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='saved_by',
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.email} saved {self.job.title}"

    class Meta:
        ordering = ['-saved_at']
        verbose_name = 'Saved Job'
        verbose_name_plural = 'Saved Jobs'
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'job'],
                name='unique_saved_job',
            )
        ]


class JobReport(models.Model):
    """
    User reports for jobs (spam, inappropriate, etc.).
    Threshold: 5 pending reports auto-flags the job.
    """
    class Reason(models.TextChoices):
        SPAM = 'spam', 'Spam / Scam'
        MISLEADING = 'misleading', 'Misleading / Fake'
        INAPPROPRIATE = 'inappropriate', 'Inappropriate Content'
        DUPLICATE = 'duplicate', 'Duplicate Posting'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        REVIEWED = 'reviewed', 'Reviewed & Action Taken'
        DISMISSED = 'dismissed', 'Dismissed (False Alarm)'

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='job_reports',
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True, help_text='Additional context from the user')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_reason_display()} report on {self.job.title}"

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'reporter'],
                name='unique_job_report',
                condition=models.Q(reporter__isnull=False)
            )
        ]
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
