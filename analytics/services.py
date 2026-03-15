from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.contrib.auth import get_user_model

from jobs.models import Job, Application
from profiles.models import EmployerProfile
from interviews.models import Interview

User = get_user_model()


def get_dashboard_analytics_data(days=30):
    """
    Returns high-level platform analytics for the admin dashboard and API endpoints.
    Results are cached based on the timeframe.
    """
    cache_key = f'admin_analytics_dashboard_data_{days}'
    data = cache.get(cache_key)

    if data is not None:
        return data

    now = timezone.now()
    start_date = now - timedelta(days=days)

    # 1. User Metrics
    total_students = User.objects.filter(role='student').count()
    total_employers = User.objects.filter(role='employer').count()
    active_in_period = User.objects.filter(last_login__gte=start_date).count()

    # 2. Job Metrics
    total_active_jobs = Job.objects.filter(status=Job.Status.ACTIVE).count()
    posted_in_period = Job.objects.filter(created_at__gte=start_date).count()
    pending_review_jobs = Job.objects.filter(status=Job.Status.PENDING_REVIEW).count()
    flagged_jobs = Job.objects.filter(is_flagged=True).count()

    # 3. Report Metrics
    from jobs.models import JobReport
    total_pending_reports = JobReport.objects.filter(status='pending').count()

    # 4. Application Metrics
    total_applications = Application.objects.count()
    apps_in_period = Application.objects.filter(applied_at__gte=start_date).count()

    # 5. Interview Metrics
    total_interviews = Interview.objects.count()
    upcoming_interviews = Interview.objects.filter(scheduled_at__gte=now).count()

    # 6. Top 5 Employers by Job Count
    top_employers_qs = EmployerProfile.objects.annotate(
        job_count=Count('jobs')
    ).order_by('-job_count')[:5]
    
    top_employers = [
        {
            "id": str(emp.id),
            "company_name": emp.company_name,
            "industry": emp.industry,
            "job_count": emp.job_count
        } for emp in top_employers_qs
    ]

    # 7. Top 5 Jobs by Application Count
    top_jobs_qs = Job.objects.annotate(
        app_count=Count('applications')
    ).order_by('-app_count')[:5]

    top_jobs = [
        {
            "id": str(job.id),
            "title": job.title,
            "company_name": job.employer.company_name if job.employer else "Unknown",
            "app_count": job.app_count
        } for job in top_jobs_qs
    ]

    # 8. Job Creation Trend (Daily)
    from django.db.models.functions import TruncDate
    trend_qs = Job.objects.filter(created_at__gte=start_date)\
        .annotate(date=TruncDate('created_at'))\
        .values('date')\
        .annotate(count=Count('id'))\
        .order_by('date')
    
    chart_trend = {
        "labels": [t['date'].strftime('%Y-%m-%d') for t in trend_qs],
        "data": [t['count'] for t in trend_qs]
    }

    # 9. Status Distribution
    status_qs = Job.objects.values('status').annotate(count=Count('id'))
    status_map = dict(Job.Status.choices)
    chart_status = {
        "labels": [status_map.get(s['status'], s['status']) for s in status_qs],
        "data": [s['count'] for s in status_qs]
    }

    data = {
        "users": {
            "total_students": total_students,
            "total_employers": total_employers,
            "active_period": active_in_period,
        },
        "jobs": {
            "total_active": total_active_jobs,
            "posted_period": posted_in_period,
            "pending_review": pending_review_jobs,
            "flagged": flagged_jobs,
        },
        "reports": {
            "pending": total_pending_reports,
        },
        "applications": {
            "total": total_applications,
            "submitted_period": apps_in_period,
        },
        "interviews": {
            "total": total_interviews,
            "upcoming": upcoming_interviews,
        },
        "top_employers": top_employers,
        "top_jobs": top_jobs,
        "charts": {
            "trend": chart_trend,
            "status": chart_status,
            "top_jobs": {
                "labels": [j['title'] for j in top_jobs],
                "data": [j['app_count'] for j in top_jobs]
            },
            "top_employers": {
                "labels": [e['company_name'] for e in top_employers],
                "data": [e['job_count'] for e in top_employers]
            }
        },
        "current_days": days
    }

    # Cache for 10 minutes (600 seconds)
    cache.set(cache_key, data, timeout=600)
    
    return data
