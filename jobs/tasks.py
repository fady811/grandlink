"""
Celery tasks for the jobs app.

Setup note: a celery beat schedule must be configured in settings.py
(or via django-celery-beat) to run `expire_stale_jobs` daily.
See settings.py CELERY_BEAT_SCHEDULE block for the schedule definition.
"""
from celery import shared_task
from django.utils import timezone


@shared_task(name='jobs.tasks.expire_stale_jobs')
def expire_stale_jobs():
    """
    Daily task: set status='expired' on any ACTIVE jobs whose deadline has passed.

    This keeps the DB status field truthful so queries and admin filters
    don't have to rely purely on the in-memory `is_expired` property.
    """
    from .models import Job

    updated = Job.objects.filter(
        status=Job.Status.ACTIVE,
        deadline__lt=timezone.now(),
    ).update(status=Job.Status.EXPIRED)

    return f"Expired {updated} job(s)."
