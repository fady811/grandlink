from rest_framework import serializers
from django.utils import timezone

from .models import Skill, Job, Application, SavedJob


# ═══════════════════════════════════════════════════════════════
#  SKILL SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name', 'category')


# ═══════════════════════════════════════════════════════════════
#  JOB SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class JobListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views — avoids loading heavy fields.
    """
    company_name = serializers.CharField(source='employer.company_name', read_only=True)
    company_logo = serializers.SerializerMethodField()
    skills = SkillSerializer(many=True, read_only=True)
    applications_count = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'title', 'company_name', 'company_logo',
            'location', 'is_remote', 'work_type', 'experience_level',
            'salary_min', 'salary_max', 'hide_salary',
            'skills', 'status', 'deadline',
            'applications_count', 'views_count', 'is_expired', 'is_saved',
            'created_at',
        )

    def get_company_logo(self, obj):
        """Placeholder for future company logo support."""
        return None

    def get_is_saved(self, obj):
        """Check if the current student has saved this job."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user.role != 'student':
            return False
        return SavedJob.objects.filter(
            student=request.user.student_profile,
            job=obj,
        ).exists()

    def to_representation(self, instance):
        """Hide salary values if hide_salary is True."""
        data = super().to_representation(instance)
        if instance.hide_salary:
            data['salary_min'] = None
            data['salary_max'] = None
        return data


class JobDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for detail / create / update views.
    """
    company_name = serializers.CharField(source='employer.company_name', read_only=True)
    company_industry = serializers.CharField(source='employer.industry', read_only=True)
    company_size = serializers.CharField(source='employer.company_size', read_only=True)
    company_website = serializers.URLField(source='employer.website', read_only=True)
    is_verified_employer = serializers.BooleanField(source='employer.is_verified', read_only=True)

    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='skills',
    )

    applications_count = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id',
            # Job info
            'title', 'description', 'requirements', 'responsibilities',
            # Classification
            'work_type', 'experience_level', 'skills', 'skill_ids',
            # Location
            'location', 'is_remote',
            # Compensation
            'salary_min', 'salary_max', 'hide_salary',
            # Status
            'status', 'deadline',
            # Company info (read-only from employer profile)
            'company_name', 'company_industry', 'company_size',
            'company_website', 'is_verified_employer',
            # Analytics
            'applications_count', 'views_count', 'is_expired', 'is_saved',
            # Dates
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'views_count', 'created_at', 'updated_at')

    # ── Validations ──────────────────────────────────────────────

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError('Job title must be at least 3 characters.')
        return value.strip()

    def validate_description(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError('Description must be at least 20 characters.')
        return value.strip()

    def validate_deadline(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError('Deadline cannot be in the past.')
        return value

    def validate(self, attrs):
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')

        # On update, merge with existing instance values
        if self.instance:
            salary_min = salary_min if salary_min is not None else self.instance.salary_min
            salary_max = salary_max if salary_max is not None else self.instance.salary_max

        if salary_min is not None and salary_max is not None:
            if salary_min > salary_max:
                raise serializers.ValidationError({
                    'salary_min': 'Minimum salary cannot exceed maximum salary.',
                })

        return attrs

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user.role != 'student':
            return False
        return SavedJob.objects.filter(
            student=request.user.student_profile,
            job=obj,
        ).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.hide_salary:
            data['salary_min'] = None
            data['salary_max'] = None
        return data


# ═══════════════════════════════════════════════════════════════
#  APPLICATION SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class ApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Used by Students to submit a new application.
    Student and Job are set in the view, not by the client.
    """
    class Meta:
        model = Application
        fields = ('id', 'cover_letter', 'resume', 'applied_at')
        read_only_fields = ('id', 'applied_at')

    def validate_resume(self, value):
        if value:
            allowed_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ]
            if value.content_type not in allowed_types:
                raise serializers.ValidationError('Only PDF and Word documents are allowed.')
            if value.size > 5 * 1024 * 1024:  # 5 MB
                raise serializers.ValidationError('File size must be under 5MB.')
        return value


class ApplicationListSerializer(serializers.ModelSerializer):
    """
    For listing applications — shows basic info.
    Used in: Student's "My Applications" & Employer's "Job Applications".
    """
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_id = serializers.UUIDField(source='job.id', read_only=True)
    company_name = serializers.CharField(source='job.employer.company_name', read_only=True)
    student_email = serializers.EmailField(source='student.user.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    student_university = serializers.CharField(source='student.university', read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'job_id', 'job_title', 'company_name',
            'student_email', 'student_name', 'student_university',
            'status', 'applied_at', 'updated_at',
        )

    def get_student_name(self, obj):
        user = obj.student.user
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name or user.email


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """
    Full application detail — for viewing a single application.
    """
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_id = serializers.UUIDField(source='job.id', read_only=True)
    company_name = serializers.CharField(source='job.employer.company_name', read_only=True)
    student_email = serializers.EmailField(source='student.user.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    student_id = serializers.UUIDField(source='student.id', read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'job_id', 'job_title', 'company_name',
            'student_id', 'student_email', 'student_name',
            'cover_letter', 'resume', 'status', 'employer_notes',
            'applied_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'job_id', 'job_title', 'company_name',
            'student_id', 'student_email', 'student_name',
            'cover_letter', 'resume', 'applied_at', 'updated_at',
        )

    def get_student_name(self, obj):
        user = obj.student.user
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name or user.email

    def to_representation(self, instance):
        """
        Hide employer_notes from students —
        only the employer who owns the job can see them.
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.role != 'employer':
            data.pop('employer_notes', None)
        return data


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Used by Employer to update application status & notes.
    """
    class Meta:
        model = Application
        fields = ('status', 'employer_notes')

    def validate_status(self, value):
        # Employer cannot set status to 'withdrawn' — that's student-only
        if value == Application.Status.WITHDRAWN:
            raise serializers.ValidationError(
                'Employers cannot withdraw applications. Only students can.'
            )
        return value


# ═══════════════════════════════════════════════════════════════
#  SAVED JOB SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class SavedJobSerializer(serializers.ModelSerializer):
    """Saved jobs list for students."""
    job = JobListSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = ('id', 'job', 'saved_at')
        read_only_fields = ('id', 'saved_at')
