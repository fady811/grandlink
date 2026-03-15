from rest_framework import serializers
from .models import SubscriptionPlan, EmployerSubscription, Invoice

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = (
            'id', 'name', 'description', 'price_monthly', 
            'price_yearly', 'max_active_jobs', 'can_feature_jobs', 
            'has_ats_access'
        )


class EmployerSubscriptionSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = EmployerSubscription
        fields = (
            'id', 'plan', 'plan_details', 'status', 
            'start_date', 'end_date', 'auto_renew', 
            'days_remaining'
        )
        read_only_fields = ('id', 'status', 'start_date', 'end_date')
