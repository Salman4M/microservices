import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class RabbitMQSettings:
    """RabbitMQ configuration settings"""
    
    # RabbitMQ connection parameters
    rabbitmq_host: str = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    rabbitmq_port: int = int(os.getenv('RABBITMQ_PORT', '5672'))
    rabbitmq_user: str = os.getenv('RABBITMQ_USER', 'admin')
    rabbitmq_pass: str = os.getenv('RABBITMQ_PASS', 'admin12345')

    @property
    def rabbitmq_url(self) -> str:
        """Build RabbitMQ URL from connection parameters"""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_pass}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

    # Exchange names
    user_exchange: str = "user_events"
    wishlist_exchange: str = "wishlist_events"
    shop_exchange: str = "shop_events"

    # Queue names
    user_events_queue: str = "wishlist_user_events_queue"

    # Exchange configuration
    exchange_type: str = "topic"
    durable: bool = True


rabbitmq_settings = RabbitMQSettings()