from celery import Celery
from celery.schedules import crontab



celery = Celery(
    "shopcart_worker",
    broker = "amqp://admin:admin12345@rabbitmq:5672//",
    backend = "redis://redis_service:6379/0"
)

celery.autodiscover_tasks(['shopcart_service'], force=True)

celery.conf.beat_schedule = {
    'sync-cart-stock-every-30-minutes': {
        'task': 'shopcart_service.tasks.sync_cart_stock',
        'schedule': crontab(minute='*/5'), 
    },
}

celery.conf.timezone = 'UTC'

#to prevent task name conflicts from other services
celery.conf.task_default_queue = 'shopcart_queue'
celery.conf.task_routes = {
    'shopcart_service.tasks.*': {'queue': 'shopcart_queue'}
}
