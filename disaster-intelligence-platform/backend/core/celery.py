"""
Celery configuration for background tasks
"""
from celery import Celery
from celery.schedules import crontab

from core.config import settings

# Create Celery app
celery_app = Celery(
    "disaster_intelligence",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["ingestion.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
)

# Beat schedule - periodic tasks
celery_app.conf.beat_schedule = {
    "ingest-weather-every-10-minutes": {
        "task": "ingestion.tasks.ingest_weather_data",
        "schedule": 600.0,  # 10 minutes
    },
    "calculate-risks-every-15-minutes": {
        "task": "ingestion.tasks.calculate_risk_scores",
        "schedule": 900.0,  # 15 minutes
    },
    "cleanup-old-data-daily": {
        "task": "ingestion.tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working"""
    print(f"Request: {self.request!r}")
    return {"status": "Celery is working!"}
