import uuid
from django.db import models
from django.conf import settings


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    university = models.CharField(max_length=255, blank=True)
    major = models.CharField(max_length=255, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    bio = models.TextField(blank=True)
    cv_file = models.FileField(upload_to='cvs/', null=True, blank=True)

    # ── Normalized skills (replaces the old JSONField) ────────────
    skills = models.ManyToManyField(
        'jobs.Skill',
        blank=True,
        related_name='student_profiles',
    )
    # Legacy field kept only during migration — will be removed in a follow-up migration
    skills_legacy = models.JSONField(default=list, blank=True)

    phone = models.CharField(max_length=20, blank=True)

    # Privacy flags
    hide_gpa = models.BooleanField(default=False)
    hide_phone = models.BooleanField(default=False)
    is_profile_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Student: {self.user.email}"


class EmployerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)  # e.g., "1-10", "11-50"
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='verified_employers',
    )
    verification_date = models.DateTimeField(null=True, blank=True)

    # Privacy
    hide_phone = models.BooleanField(default=False)
    is_profile_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Employer: {self.company_name}"