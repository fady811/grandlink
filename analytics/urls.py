from django.urls import path
from .views import AnalyticsAPIView, admin_analytics_view

urlpatterns = [
    # API Endpoint
    path('api/admin/analytics/', AnalyticsAPIView.as_view(), name='api-admin-analytics'),
]
