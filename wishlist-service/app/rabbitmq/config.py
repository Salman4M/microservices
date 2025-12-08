import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class RabbitMQSettings:

    # RabbitMQ connection parameters (read from environment variables using os.getenv)
    rabbitmq_host: str = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    rabbitmq_port: int = int(os.getenv('RABBITMQ_PORT', '5672'))
    rabbitmq_user: str = os.getenv('RABBITMQ_USER', 'admin')
    rabbitmq_pass: str = os.getenv('RABBITMQ_PASS', 'admin12345')

    # Build RabbitMQ URL from connection parameters (for aio_pika compatibility)
    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_pass}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

    user_exchange: str = "user_events"
    wishlist_exchange: str = "wishlist_events"

    user_events_queue: str = "wishlist_user_events_queue"

    exchange_type: str = "topic"

    durable: bool = True


rabbitmq_settings = RabbitMQSettings()