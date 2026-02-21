from django.urls import path
from .views import StudentProfileDetailView, EmployerProfileDetailView, PrivacySettingsView

urlpatterns = [
    path('student/', StudentProfileDetailView.as_view(), name='my-student-profile'),
    path('student/<uuid:user_id>/', StudentProfileDetailView.as_view(), name='student-profile-by-user'),
    path('employer/', EmployerProfileDetailView.as_view(), name='my-employer-profile'),
    path('employer/<uuid:user_id>/', EmployerProfileDetailView.as_view(), name='employer-profile-by-user'),
    path('privacy/', PrivacySettingsView.as_view(), name='privacy-settings'),
]