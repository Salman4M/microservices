#!/usr/bin/env python3
import pika
import json
import os
import django
import sys
from pathlib import Path
import logging

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger("user_events")



class ShopEventConsumer:
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
    
    def handle_shop_approved(self, message: dict):
        try:
            user_uuid = message.get('user_uuid')
            shop_id = message.get('shop_id')
            
            if not user_uuid:
                logger.warning("Missing user_uuid in shop.approved event")
                return False
            
            user = User.objects.get(id=user_uuid)
            user.is_shop_owner = True
            user.save()
            
            logger.info(f"User {user_uuid} is now shop owner (shop={shop_id})")
            return True
            
        except User.DoesNotExist:
            logger.error(f"User {user_uuid} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to handle shop.approved event: {e}")
            return False
    
    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            event_type = message.get('event_type')
            
            logger.info(f"Received event: {event_type}")
            
            if event_type == 'shop.approved':
                success = self.handle_shop_approved(message)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                success = True
            
            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        import time
        
        while True:
            try:
                connection = self.get_connection()
                channel = connection.channel()
                
                channel.exchange_declare(
                    exchange='shop_events',
                    exchange_type='topic',
                    durable=True
                )
                
                queue_name = 'user_shop_events'
                channel.queue_declare(queue=queue_name, durable=True)
                
                channel.queue_bind(
                    exchange='shop_events',
                    queue=queue_name,
                    routing_key='shop.approved'
                )
                
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self.callback
                )
                
                logger.info("User service listening for shop.approved events…")
                channel.start_consuming()
                
            except KeyboardInterrupt:
                logger.info("Stopping consumer…")
                break
            except Exception as e:
                logger.error(f"Connection error: {e}")
                time.sleep(5)


if __name__ == '__main__':
    consumer = ShopEventConsumer()
    consumer.start_consuming()