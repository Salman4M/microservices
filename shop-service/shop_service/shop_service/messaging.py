import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()


class RabbitMQPublisher:
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.user = os.getenv('RABBITMQ_USER', 'admin')
        self.password = os.getenv('RABBITMQ_PASS', 'admin12345')
        
    def get_connection(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        return pika.BlockingConnection(parameters)
    
    def publish_shop_created(self, user_uuid: str, shop_id: str):
        """Publish shop.created event when a shop is created"""
        try:
            connection = self.get_connection()
            channel = connection.channel()
            
            channel.exchange_declare(
                exchange='shop_events',
                exchange_type='topic',
                durable=True
            )
            
            message = {
                'event_type': 'shop.created',
                'user_uuid': str(user_uuid),
                'shop_id': str(shop_id),
                'is_shop_owner': True  # User is now a seller
            }
            
            channel.basic_publish(
                exchange='shop_events',
                routing_key='shop.created',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            print(f"✅ Published shop.created event for user {user_uuid}, shop {shop_id}")
            connection.close()
            
        except Exception as e:
            print(f"❌ Failed to publish shop.created event: {e}")


publisher = RabbitMQPublisher()