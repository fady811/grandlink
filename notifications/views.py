from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import QuerySet

from core.pagination import StandardPagination
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """
    GET /api/notifications/
    List notifications for current user. Unread first, then by date.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        # Primary sort: is_read (False comes first), then by created_at desc
        return Notification.objects.filter(user=self.request.user).order_by('is_read', '-created_at')


class NotificationUnreadCountView(APIView):
    """
    GET /api/notifications/unread-count/
    Returns the count of unread notifications.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class NotificationMarkReadView(generics.UpdateAPIView):
    """
    PATCH /api/notifications/<uuid>/read/
    Mark a single notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.all()
    http_method_names = ['patch']

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def patch(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'message': 'Notification marked as read.', 'id': notification.id})


class NotificationMarkAllReadView(APIView):
    """
    POST /api/notifications/mark-all-read/
    Mark all unread notifications for the current user as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'message': f'{updated} notifications marked as read.',
            'count': updated
        })
