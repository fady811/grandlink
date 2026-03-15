from rest_framework import generics, permissions, status, response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import SupportTicket, TicketReply
from .serializers import (
    SupportTicketSerializer, 
    SupportTicketDetailSerializer, 
    TicketReplySerializer,
    SupportTicketStatusUpdateSerializer
)
from .permissions import IsTicketOwnerOrAdmin
from notifications.utils import notify
from notifications.models import Notification

class SupportTicketListCreateView(generics.ListCreateAPIView):
    """
    POST /api/support/tickets/ — create ticket (authenticated)
    GET /api/support/tickets/ — list own tickets (students/employers) or all (admin)
    """
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SupportTicketDetailView(generics.RetrieveAPIView):
    """
    GET /api/support/tickets/<uuid>/ — detail with replies
    """
    serializer_class = SupportTicketDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsTicketOwnerOrAdmin]
    queryset = SupportTicket.objects.all()


class TicketReplyCreateView(generics.CreateAPIView):
    """
    POST /api/support/tickets/<uuid>/reply/ — add reply (ticket owner or admin)
    """
    serializer_class = TicketReplySerializer
    permission_classes = [permissions.IsAuthenticated, IsTicketOwnerOrAdmin]

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('pk')
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        
        # Check permissions via get_object manual check if needed, 
        # but generic views handle it if we used RetrieveAPIView.
        # Here we manually ensure the user can reply to THIS ticket.
        self.check_object_permissions(self.request, ticket)

        is_staff = self.request.user.is_staff
        reply = serializer.save(
            ticket=ticket, 
            author=self.request.user,
            is_staff_reply=is_staff
        )

        # Notify ticket owner if admin replies
        if is_staff and ticket.user != self.request.user:
            notify(
                user=ticket.user,
                type=Notification.NotificationType.ANNOUNCEMENT, # Generic or we could add a support type
                message=f"Admin replied to your ticket: {ticket.subject}",
                related_object_id=ticket.id
            )


class SupportTicketStatusUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/support/tickets/<uuid>/status/ — update status (admin only)
    """
    serializer_class = SupportTicketStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset = SupportTicket.objects.all()
    http_method_names = ['patch']

    def perform_update(self, serializer):
        ticket = serializer.save()
        
        # Notify ticket owner about status change
        notify(
            user=ticket.user,
            type=Notification.NotificationType.ANNOUNCEMENT,
            message=f"Ticket status updated to {ticket.get_status_display()}: {ticket.subject}",
            related_object_id=ticket.id
        )
