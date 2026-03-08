"""
Celery application instance for GradLink.

Usage:
    Start worker:  celery -A core worker -l info
    Start beat:    celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('gradlink')

# Load config from Django settings, using the CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
