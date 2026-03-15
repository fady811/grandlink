from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SupportTicket, TicketReply

User = get_user_model()

class TicketReplySerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)

    class Meta:
        model = TicketReply
        fields = (
            'id', 'author_email', 'message', 
            'is_staff_reply', 'created_at'
        )
        read_only_fields = ('id', 'is_staff_reply', 'author_email', 'created_at')


class SupportTicketSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = SupportTicket
        fields = (
            'id', 'user_email', 'subject', 'message', 
            'category', 'category_display', 'status', 'status_display',
            'priority', 'priority_display', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user_email', 'status', 'status_display', 
            'category_display', 'priority_display', 
            'created_at', 'updated_at'
        )


class SupportTicketDetailSerializer(SupportTicketSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)

    class Meta(SupportTicketSerializer.Meta):
        fields = SupportTicketSerializer.Meta.fields + ('replies',)


class SupportTicketStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ('status',)
