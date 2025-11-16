from celery import Celery
from celery.schedules import crontab



celery = Celery(
    "worker",
    broker = "amqp://admin:admin12345@rabbitmq:5672//",
    backend = "redis://redis_service:6379/0"
)

celery.autodiscover_tasks(['shopcart_service'])

celery.conf.beat_schedule = {
    'sync-cart-stock-every-30-minutes': {
        'task': 'shopcart_service.tasks.sync_cart_stock',
        'schedule': crontab(minute='*/5'), 
    },
}

celery.conf.timezone = 'UTC'
