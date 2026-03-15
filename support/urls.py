from django.urls import path
from .views import (
    SupportTicketListCreateView,
    SupportTicketDetailView,
    TicketReplyCreateView,
    SupportTicketStatusUpdateView
)

urlpatterns = [
    path('tickets/', SupportTicketListCreateView.as_view(), name='ticket-list-create'),
    path('tickets/<uuid:pk>/', SupportTicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<uuid:pk>/reply/', TicketReplyCreateView.as_view(), name='ticket-reply'),
    path('tickets/<uuid:pk>/status/', SupportTicketStatusUpdateView.as_view(), name='ticket-status-update'),
]
