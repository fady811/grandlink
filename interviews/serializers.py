from rest_framework import serializers
from django.utils import timezone
from .models import Interview, InterviewFeedback
from jobs.models import Application


class InterviewCreateSerializer(serializers.ModelSerializer):
    """Used by employers to schedule a new interview."""

    application_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Interview
        fields = (
            'id', 'application_id', 'title', 'description',
            'interview_type', 'scheduled_at', 'duration_minutes',
            'location', 'meeting_link',
        )
        read_only_fields = ('id',)

    def validate_application_id(self, value):
        """Ensure the application exists and belongs to the current employer."""
        request = self.context['request']
        try:
            application = Application.objects.select_related(
                'job__employer__user'
            ).get(id=value)
        except Application.DoesNotExist:
            raise serializers.ValidationError("Application not found.")

        if application.job.employer.user != request.user:
            raise serializers.ValidationError("You can only schedule interviews for your own job applications.")

        if application.status not in ('interview', 'shortlisted', 'reviewing'):
            raise serializers.ValidationError(
                f"Cannot schedule an interview for an application with status '{application.get_status_display()}'."
            )

        return value

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Interview must be scheduled in the future.")
        return value

    def validate(self, attrs):
        interview_type = attrs.get('interview_type', 'video')
        if interview_type == 'video' and not attrs.get('meeting_link'):
            raise serializers.ValidationError(
                {"meeting_link": "A meeting link is required for video interviews."}
            )
        if interview_type == 'in_person' and not attrs.get('location'):
            raise serializers.ValidationError(
                {"location": "A location is required for in-person interviews."}
            )
        return attrs

    def create(self, validated_data):
        application_id = validated_data.pop('application_id')
        application = Application.objects.get(id=application_id)

        # Auto-transition application status to 'interview' if not already
        if application.status != Application.Status.INTERVIEW:
            application.status = Application.Status.INTERVIEW
            application.save(update_fields=['status', 'updated_at'])

        interview = Interview.objects.create(
            application=application,
            scheduled_by=self.context['request'].user,
            **validated_data,
        )
        return interview


class InterviewListSerializer(serializers.ModelSerializer):
    """Compact list view of interviews."""

    job_title = serializers.CharField(source='application.job.title', read_only=True)
    company_name = serializers.CharField(source='application.job.employer.company_name', read_only=True)
    student_email = serializers.EmailField(source='application.student.user.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    has_feedback = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = (
            'id', 'title', 'interview_type', 'scheduled_at',
            'duration_minutes', 'status',
            'job_title', 'company_name', 'student_email', 'student_name',
            'has_feedback', 'created_at',
        )

    def get_student_name(self, obj):
        user = obj.application.student.user
        return user.get_full_name() or user.email

    def get_has_feedback(self, obj):
        return hasattr(obj, 'feedback')


class InterviewDetailSerializer(serializers.ModelSerializer):
    """Full detail view of a single interview."""

    job_title = serializers.CharField(source='application.job.title', read_only=True)
    job_id = serializers.UUIDField(source='application.job.id', read_only=True)
    company_name = serializers.CharField(source='application.job.employer.company_name', read_only=True)
    student_email = serializers.EmailField(source='application.student.user.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    application_id = serializers.UUIDField(source='application.id', read_only=True)
    feedback = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = (
            'id', 'application_id', 'title', 'description',
            'interview_type', 'scheduled_at', 'duration_minutes',
            'location', 'meeting_link', 'status', 'cancellation_reason',
            'job_title', 'job_id', 'company_name',
            'student_email', 'student_name',
            'feedback',
            'created_at', 'updated_at',
        )

    def get_student_name(self, obj):
        user = obj.application.student.user
        return user.get_full_name() or user.email

    def get_feedback(self, obj):
        try:
            fb = obj.feedback
            return InterviewFeedbackSerializer(fb).data
        except InterviewFeedback.DoesNotExist:
            return None


class InterviewUpdateSerializer(serializers.ModelSerializer):
    """Used by employers to reschedule or update an interview."""

    class Meta:
        model = Interview
        fields = (
            'title', 'description', 'interview_type',
            'scheduled_at', 'duration_minutes',
            'location', 'meeting_link', 'status',
            'cancellation_reason',
        )

    def validate_scheduled_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Interview must be scheduled in the future.")
        return value

    def validate_status(self, value):
        current = self.instance.status
        allowed_transitions = {
            'scheduled': ['confirmed', 'cancelled', 'no_show', 'completed'],
            'confirmed': ['completed', 'cancelled', 'no_show'],
            'completed': [],      # Terminal
            'cancelled': [],      # Terminal
            'no_show': [],        # Terminal
        }
        if value != current and value not in allowed_transitions.get(current, []):
            raise serializers.ValidationError(
                f"Cannot transition from '{current}' to '{value}'."
            )
        return value

    def validate(self, attrs):
        # If cancelling, require a reason
        new_status = attrs.get('status')
        if new_status == 'cancelled':
            reason = attrs.get('cancellation_reason') or (self.instance and self.instance.cancellation_reason)
            if not reason:
                raise serializers.ValidationError(
                    {"cancellation_reason": "A reason is required when cancelling an interview."}
                )
        return attrs


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    """Create and read interview feedback."""

    submitted_by_email = serializers.EmailField(source='submitted_by.email', read_only=True)

    class Meta:
        model = InterviewFeedback
        fields = (
            'id', 'rating', 'technical_rating', 'communication_rating',
            'cultural_fit_rating', 'strengths', 'weaknesses', 'notes',
            'recommendation', 'submitted_by_email', 'created_at',
        )
        read_only_fields = ('id', 'submitted_by_email', 'created_at')


class InterviewStatsSerializer(serializers.Serializer):
    """Aggregated pipeline stats for an employer."""

    total_interviews = serializers.IntegerField()
    scheduled = serializers.IntegerField()
    confirmed = serializers.IntegerField()
    completed = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    no_show = serializers.IntegerField()
    avg_rating = serializers.FloatField(allow_null=True)
    recommendation_breakdown = serializers.DictField()
