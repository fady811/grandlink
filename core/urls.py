from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from analytics.views import admin_analytics_view

urlpatterns = [
    path('admin/analytics/', admin_analytics_view, name='admin_analytics'),
    path('admin/', admin.site.urls),
    path('', include('analytics.urls')),
    path('api/auth/', include('authentication.urls')),
    path('api/profiles/', include('profiles.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/interviews/', include('interviews.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/support/', include('support.urls')),
    path('api/billing/', include('billing.urls')),
    # ── API Documentation (Swagger) ──────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)