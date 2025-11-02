import pika
import json
import os
from django.conf import settings


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
    
    def publish_user_created(self, user_uuid: str, email: str, is_active: bool):
        try:
            connection = self.get_connection()
            channel = connection.channel()
            
            channel.exchange_declare(
                exchange='user_events',
                exchange_type='topic',
                durable=True
            )
            
            message = {
                'event_type': 'user.created',
                'user_uuid': str(user_uuid),
                'email': email,
                'is_active': is_active
            }
            
            channel.basic_publish(
                exchange='user_events',
                routing_key='user.created',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            print(f" Published user.created event for {user_uuid}")
            connection.close()
            
        except Exception as e:
            print(f" Failed to publish message: {e}")


publisher = RabbitMQPublisher()