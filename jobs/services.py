"""
Service layer for job approval workflow.
Called from both the admin panel and API views to keep logic DRY.
"""
from django.utils import timezone


def approve_job(job, admin_user):
    """
    Approve a pending_review job.
    Sets status to active, records reviewer info.
    Notifications are handled by signals.
    """
    from .models import Job

    job.status = Job.Status.ACTIVE
    job.reviewed_by = admin_user
    job.reviewed_at = timezone.now()
    job.rejection_reason = ''
    job.save(update_fields=[
        'status', 'reviewed_by', 'reviewed_at',
        'rejection_reason', 'updated_at',
    ])


def reject_job(job, admin_user, reason):
    """
    Reject a pending_review job.
    Sets status back to draft, records rejection reason.
    Notifications are handled by signals.
    """
    from .models import Job

    job.status = Job.Status.DRAFT
    job.reviewed_by = admin_user
    job.reviewed_at = timezone.now()
    job.rejection_reason = reason
    job.save(update_fields=[
        'status', 'reviewed_by', 'reviewed_at',
        'rejection_reason', 'updated_at',
    ])


def process_job_report(job, reporter, reason, details):
    """
    Process a new job report.
    If pending reports hit 5, auto-flag the job.
    """
    from django.contrib.auth import get_user_model
    from .models import JobReport
    from notifications.utils import notify
    from notifications.models import Notification

    User = get_user_model()

    JobReport.objects.create(
        job=job,
        reporter=reporter,
        reason=reason,
        details=details,
        status=JobReport.Status.PENDING
    )

    pending_count = job.reports.filter(status=JobReport.Status.PENDING).count()

    if pending_count >= 5 and not job.is_flagged:
        # Auto-flag the job
        job.is_flagged = True
        job.save(update_fields=['is_flagged', 'updated_at'])

        # Notify all admins
        admins = User.objects.filter(is_staff=True, is_active=True)
        msg = f'The job "{job.title}" has received {pending_count} pending reports and was auto-hidden.'
        for admin in admins:
            notify(
                user=admin,
                type=Notification.NotificationType.JOB_REJECTED, # Best fit for flagging
                message=msg,
                related_object_id=job.id
            )

        # Notify the employer
        notify(
            user=job.employer.user,
            type=Notification.NotificationType.JOB_REJECTED,
            message=f'Your job "{job.title}" has received multiple community reports and is temporarily hidden.',
            related_object_id=job.id
        )


def resolve_job_report(job):
    """
    Called when an admin dismisses/reviews reports.
    If pending reports drop below 5, unflag the job.
    """
    from .models import JobReport
    
    pending_count = job.reports.filter(status=JobReport.Status.PENDING).count()
    
    if pending_count < 5 and job.is_flagged:
        job.is_flagged = False
        job.save(update_fields=['is_flagged', 'updated_at'])
