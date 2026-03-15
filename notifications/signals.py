from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from jobs.models import Job, Application
from interviews.models import Interview
from .utils import notify
from .models import Notification

@receiver(pre_save, sender=Job)
def job_pre_save(sender, instance, **kwargs):
    """Store old status to detect change in post_save."""
    try:
        instance._old_status = Job.objects.get(pk=instance.pk).status
    except Job.DoesNotExist:
        instance._old_status = None

@receiver(post_save, sender=Job)
def job_post_save(sender, instance, created, **kwargs):
    if created: return
    
    old_status = getattr(instance, '_old_status', None)
    if old_status != instance.status:
        if instance.status == Job.Status.ACTIVE:
            notify(
                user=instance.employer.user,
                type=Notification.NotificationType.JOB_APPROVED,
                message=f'Your job "{instance.title}" has been approved!',
                related_object_id=instance.id
            )
        elif instance.status == Job.Status.DRAFT and instance.rejection_reason:
            notify(
                user=instance.employer.user,
                type=Notification.NotificationType.JOB_REJECTED,
                message=f'Your job "{instance.title}" was rejected. Reason: {instance.rejection_reason}',
                related_object_id=instance.id
            )

@receiver(pre_save, sender=Application)
def application_pre_save(sender, instance, **kwargs):
    try:
        instance._old_status = Application.objects.get(pk=instance.pk).status
    except Application.DoesNotExist:
        instance._old_status = None

@receiver(post_save, sender=Application)
def application_post_save(sender, instance, created, **kwargs):
    if created:
        notify(
            user=instance.job.employer.user,
            type=Notification.NotificationType.APPLICATION_RECEIVED,
            message=f'New application for "{instance.job.title}"',
            related_object_id=instance.id
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status != instance.status:
            notify(
                user=instance.student.user,
                type=Notification.NotificationType.APPLICATION_STATUS_CHANGED,
                message=f'Your application for "{instance.job.title}" is now: {instance.get_status_display()}',
                related_object_id=instance.id
            )

@receiver(pre_save, sender=Interview)
def interview_pre_save(sender, instance, **kwargs):
    try:
        instance._old_status = Interview.objects.get(pk=instance.pk).status
    except Interview.DoesNotExist:
        instance._old_status = None

@receiver(post_save, sender=Interview)
def interview_post_save(sender, instance, created, **kwargs):
    if created:
        notify(
            user=instance.application.student.user,
            type=Notification.NotificationType.INTERVIEW_SCHEDULED,
            message=f'Interview scheduled for "{instance.job.title}"',
            related_object_id=instance.id
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status != instance.status:
            if instance.status == Interview.Status.CONFIRMED:
                notify(
                    user=instance.job.employer.user,
                    type=Notification.NotificationType.INTERVIEW_CONFIRMED,
                    message=f'Student confirmed interview for "{instance.job.title}"',
                    related_object_id=instance.id
                )
            elif instance.status == Interview.Status.CANCELLED:
                msg = f'Interview for "{instance.job.title}" cancelled.'
                notify(instance.student.user, Notification.NotificationType.INTERVIEW_CANCELLED, msg, instance.id)
                notify(instance.job.employer.user, Notification.NotificationType.INTERVIEW_CANCELLED, msg, instance.id)
