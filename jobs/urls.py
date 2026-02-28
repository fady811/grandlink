from django.urls import path
from .views import (
    # Skills
    SkillListView,
    # Jobs
    JobListCreateView,
    JobDetailView,
    MyJobsListView,
    # Applications
    ApplyToJobView,
    MyApplicationsListView,
    JobApplicationsListView,
    ApplicationDetailView,
    ApplicationStatusUpdateView,
    WithdrawApplicationView,
    # Saved Jobs
    SavedJobsListView,
    SaveJobView,
    UnsaveJobView,
)

urlpatterns = [
    # ── Skills ───────────────────────────────────────────────────
    path('skills/', SkillListView.as_view(), name='skill-list'),

    # ── Jobs CRUD ────────────────────────────────────────────────
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<uuid:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('my-jobs/', MyJobsListView.as_view(), name='my-jobs'),

    # ── Applications ─────────────────────────────────────────────
    path('<uuid:job_id>/apply/', ApplyToJobView.as_view(), name='apply-to-job'),
    path('<uuid:job_id>/applications/', JobApplicationsListView.as_view(), name='job-applications'),
    path('my-applications/', MyApplicationsListView.as_view(), name='my-applications'),
    path('applications/<uuid:pk>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('applications/<uuid:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application-status-update'),
    path('applications/<uuid:pk>/withdraw/', WithdrawApplicationView.as_view(), name='withdraw-application'),

    # ── Saved Jobs ───────────────────────────────────────────────
    path('saved/', SavedJobsListView.as_view(), name='saved-jobs'),
    path('<uuid:job_id>/save/', SaveJobView.as_view(), name='save-job'),
    path('<uuid:job_id>/unsave/', UnsaveJobView.as_view(), name='unsave-job'),
]
