from django.urls import path
from .views import (
    InterviewListCreateView,
    InterviewDetailView,
    InterviewConfirmView,
    InterviewFeedbackCreateView,
    InterviewFeedbackDetailView,
    UpcomingInterviewsView,
    InterviewStatsView,
)

urlpatterns = [
    # ── Dashboard ────────────────────────────────────────────────
    path('upcoming/', UpcomingInterviewsView.as_view(), name='interview-upcoming'),
    path('stats/', InterviewStatsView.as_view(), name='interview-stats'),

    # ── CRUD ─────────────────────────────────────────────────────
    path('', InterviewListCreateView.as_view(), name='interview-list-create'),
    path('<uuid:pk>/', InterviewDetailView.as_view(), name='interview-detail'),

    # ── Student Actions ──────────────────────────────────────────
    path('<uuid:pk>/confirm/', InterviewConfirmView.as_view(), name='interview-confirm'),

    # ── Feedback ─────────────────────────────────────────────────
    path('<uuid:pk>/feedback/', InterviewFeedbackCreateView.as_view(), name='interview-feedback-create'),
    path('<uuid:pk>/feedback/detail/', InterviewFeedbackDetailView.as_view(), name='interview-feedback-detail'),
]
