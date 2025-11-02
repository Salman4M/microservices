#!/usr/bin/env python3
import pika
import json
import os
import django
import sys
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


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
    
    def handle_shop_created(self, message: dict):
        """Handle shop.created event"""
        try:
            user_uuid = message.get('user_uuid')
            shop_id = message.get('shop_id')
            
            if not user_uuid:
                print(f"⚠️ Missing user_uuid in shop.created event")
                return False
            
            # Update user to be shop owner
            user = User.objects.get(id=user_uuid)
            user.is_shop_owner = True
            user.save()
            
            print(f"✅ User {user_uuid} is now a shop owner (shop: {shop_id})")
            return True
            
        except User.DoesNotExist:
            print(f"❌ User {user_uuid} not found")
            return False
        except Exception as e:
            print(f"❌ Failed to handle shop.created event: {e}")
            return False
    
    def callback(self, ch, method, properties, body):
        """Handle incoming messages"""
        try:
            message = json.loads(body)
            event_type = message.get('event_type')
            
            print(f"📨 Received event: {event_type}")
            
            success = False
            if event_type == 'shop.created':
                success = self.handle_shop_created(message)
            else:
                print(f"⚠️ Unknown event type: {event_type}")
                success = True  # Ack unknown events
            
            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Start listening for shop events"""
        import time
        
        while True:
            try:
                connection = self.get_connection()
                channel = connection.channel()
                
                # Declare exchange
                channel.exchange_declare(
                    exchange='shop_events',
                    exchange_type='topic',
                    durable=True
                )
                
                # Declare queue
                queue_name = 'user_shop_events'
                channel.queue_declare(queue=queue_name, durable=True)
                
                # Bind queue to shop events
                channel.queue_bind(
                    exchange='shop_events',
                    queue=queue_name,
                    routing_key='shop.created'
                )
                
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self.callback
                )
                
                print('🎧 User service listening for shop.created events...')
                channel.start_consuming()
                
            except KeyboardInterrupt:
                print("🛑 Stopping consumer...")
                break
            except Exception as e:
                print(f"❌ Connection error: {e}")
                print("⏳ Retrying in 5 seconds...")
                time.sleep(5)


if __name__ == '__main__':
    consumer = ShopEventConsumer()
    consumer.start_consuming()