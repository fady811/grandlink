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

    # ── Analytics ────────────────────────────────────────────────
    views_count = models.PositiveIntegerField(default=0)

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

    class Meta:
        ordering = ['-created_at']
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
