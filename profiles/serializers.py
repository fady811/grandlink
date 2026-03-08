from rest_framework import serializers
from .models import StudentProfile, EmployerProfile


class StudentProfileSerializer(serializers.ModelSerializer):
    # Expose skills as a list of skill IDs for write, nested objects for read
    from jobs.serializers import SkillSerializer  # local import to avoid circular
    skill_ids = serializers.PrimaryKeyRelatedField(
        source='skills',
        many=True,
        write_only=True,
        required=False,
        queryset=__import__('jobs.models', fromlist=['Skill']).Skill.objects.all(),
    )

    class Meta:
        model = StudentProfile
        exclude = ('user', 'skills_legacy')  # hide legacy field from API

    def to_representation(self, instance):
        """Apply privacy rules based on requesting user"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request:
            return data

        user = request.user
        if not user.is_authenticated:
            return {}

        # If admin or owner, show all
        if user.is_staff or user == instance.user:
            return data

        # Otherwise apply privacy flags
        if instance.hide_gpa:
            data['gpa'] = None
        if instance.hide_phone:
            data['phone'] = None
        # If profile not public, return only basic info
        if not instance.is_profile_public:
            allowed = ['university', 'major', 'graduation_year', 'bio', 'skills']
            data = {k: v for k, v in data.items() if k in allowed}
        return data


class EmployerProfileSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmployerProfile
        exclude = ('user',)

    def get_logo_url(self, obj):
        """Return absolute URL for company logo if it exists."""
        if not obj.logo:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return obj.logo.url

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request:
            return data

        user = request.user
        if not user.is_authenticated:
            return {}

        if user.is_staff or user == instance.user:
            return data

        if instance.hide_phone:
            data['phone'] = None
        if not instance.is_profile_public:
            allowed = ['company_name', 'industry', 'company_size', 'website', 'logo_url']
            data = {k: v for k, v in data.items() if k in allowed}
        return data