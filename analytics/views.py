from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from .services import get_dashboard_analytics_data


class AnalyticsAPIView(APIView):
    """
    GET /api/admin/analytics/?days=30
    Returns aggregated JSON payload of platform health.
    Authorized for staff users only.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        try:
            days = int(request.query_params.get('days', 30))
        except ValueError:
            days = 30
        data = get_dashboard_analytics_data(days=days)
        return Response(data)


@staff_member_required
def admin_analytics_view(request):
    """
    A custom view embedded into the Django Admin ecosystem (Jazzmin).
    It fetches the same cached data as the API.
    """
    from django.contrib import admin
    
    try:
        days = int(request.GET.get('days', 30))
    except ValueError:
        days = 30

    data = get_dashboard_analytics_data(days=days)

    # Get standard admin context (provides available_apps for sidebar)
    context = admin.site.each_context(request)
    
    context.update({
        **data,
        'title': 'Platform Analytics',
        'site_title': 'GradLink Admin',
        'site_header': 'GradLink Analytics',
        'has_permission': request.user.is_active and request.user.is_staff,
    })
    
    return render(request, 'admin/analytics_dashboard.html', context)
