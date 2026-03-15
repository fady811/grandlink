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


@shared_task(name='jobs.tasks.send_job_status_email')
def send_job_status_email(job_id: str, action: str):
    """
    Send approval or rejection email to the employer.

    Args:
        job_id: UUID string of the Job
        action: 'approved' or 'rejected'
    """
    from django.conf import settings
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from .models import Job

    job = Job.objects.select_related('employer__user').get(id=job_id)
    employer_email = job.employer.user.email

    if action == 'approved':
        subject = f'✅ Your job "{job.title}" has been approved!'
        template = 'emails/job_approved.html'
    elif action == 'flagged':
        subject = f'🚨 Job Temporarily Hidden: "{job.title}"'
        template = 'emails/job_flagged.html'
    else:
        subject = f'Your job "{job.title}" needs changes'
        template = 'emails/job_rejected.html'

    context = {
        'job': job,
        'employer_name': job.employer.company_name,
        'rejection_reason': job.rejection_reason,
    }

    html_message = render_to_string(template, context)
    send_mail(
        subject=subject,
        message='',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[employer_email],
        html_message=html_message,
        fail_silently=False,
    )
