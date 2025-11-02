# order-service/order_service/utils/rabbitmq_producer.py
import pika
import json
import os
import logging

logger = logging.getLogger(__name__)


class RabbitMQProducer:
    """Producer to publish events to RabbitMQ"""
    
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.getenv('RABBITMQ_PORT', '5672'))
        self.user = os.getenv('RABBITMQ_USER', 'admin')
        self.password = os.getenv('RABBITMQ_PASS', 'admin12345')
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange for order events
            self.channel.exchange_declare(
                exchange='order_events',
                exchange_type='topic',
                durable=True
            )
            
            print("✅ Connected to RabbitMQ")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to RabbitMQ: {e}")
            return False
    
    def publish_order_created(self, order_id: int, user_uuid: str, cart_id: int):
        """
        Publish order.created event
        This tells shopcart service to clear the cart
        """
        if not self.channel or self.connection.is_closed:
            if not self.connect():
                return False
        
        try:
            message = {
                'event': 'order.created',
                'data': {
                    'order_id': order_id,
                    'user_uuid': str(user_uuid),
                    'cart_id': cart_id,
                }
            }
            
            self.channel.basic_publish(
                exchange='order_events',
                routing_key='order.created',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            print(f"📤 Published order.created event for order {order_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to publish order.created event: {e}")
            return False
    
    def close(self):
        """Close connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print("🔌 RabbitMQ connection closed")
        except Exception as e:
            print(f"Error closing RabbitMQ connection: {e}")


# Singleton instance
rabbitmq_producer = RabbitMQProducer()