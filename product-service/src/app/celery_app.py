from celery import Celery
from celery.schedules import crontab
import os

celery = Celery(
    "product_service",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "rpc://")
)

# Automatically discover tasks in the service
celery.autodiscover_tasks(['src.app.tasks'])

# Beat schedule: daily check of low stock
celery.conf.beat_schedule = {
    'check-low-stock-daily': {
        'task': 'product_service.tasks.check_low_stock',
        'schedule': crontab(hour=0, minute=0),  # once per day
    },
}

celery.conf.timezone = 'UTC'