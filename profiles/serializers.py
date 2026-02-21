from rest_framework import serializers
from .models import StudentProfile, EmployerProfile
from django.conf import settings

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        exclude = ('user',)  # We'll set user from context

    def to_representation(self, instance):
        """Apply privacy rules based on requesting user"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request:
            return data

        user = request.user
        # If not authenticated, only public data (but we already require auth globally)
        if not user.is_authenticated:
            # Minimal data (name only) – but we'll let permission classes handle
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
            # Keep only non-sensitive fields: university, major, grad_year, bio, skills
            allowed = ['university', 'major', 'graduation_year', 'bio', 'skills']
            data = {k: v for k, v in data.items() if k in allowed}
        return data


class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerProfile
        exclude = ('user',)

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
            allowed = ['company_name', 'industry', 'company_size', 'website']
            data = {k: v for k, v in data.items() if k in allowed}
        return data