from celery import Celery

celery = Celery(
    "worker",
    broker = "amqp://admin:admin12345@rabbitmq:5672//",
    backend = "redis://redis_service:6379/0"
)

