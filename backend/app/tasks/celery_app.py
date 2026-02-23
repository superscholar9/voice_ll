"""Celery application setup."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


celery_app = Celery(
    "voice_ll",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_default_queue=settings.COVER_QUEUE_NAME,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_track_started=True,
    task_time_limit=60 * 60,
    task_soft_time_limit=55 * 60,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-cover-assets": {
        "task": "cover.cleanup_expired_assets",
        "schedule": crontab(minute=0),  # Run every hour at minute 0
    },
}

