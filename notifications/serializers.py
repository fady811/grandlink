from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for listing notifications."""

    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id', 'type', 'type_display', 'message',
            'related_object_id', 'is_read', 'created_at',
        )
        read_only_fields = fields
