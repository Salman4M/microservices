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
        self.host = os.getenv('RABBITMQ_HOST')
        self.port = int(os.getenv('RABBITMQ_PORT'))
        self.user = os.getenv('RABBITMQ_USER')
        self.password = os.getenv('RABBITMQ_PASS')
        
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
                logger.warning("⚠️ Missing user_uuid in shop.approved event")
                return False
            
            user = User.objects.get(id=user_uuid)
            user.is_shop_owner = True
            user.save()
            
            logger.info(f"✅ User {user_uuid} is now shop owner (shop={shop_id})")
            return True
            
        except User.DoesNotExist:
            logger.error(f"❌ User {user_uuid} not found")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to handle shop.approved event: {e}")
            return False
        
    def handle_shop_deleted(self, message: dict):
        try:
            user_uuid = message.get('user_uuid')
            shop_id = message.get('shop_id')
            
            if not user_uuid:
                logger.warning("⚠️ Missing user_uuid in shop.deleted event")
                return False
            
            user = User.objects.get(id=user_uuid)
            user.is_shop_owner = False
            user.save()
            
            logger.info(f"✅ User {user_uuid} is no longer shop owner (shop={shop_id})")
            return True
            
        except User.DoesNotExist:
            logger.error(f"❌ User {user_uuid} not found")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to handle shop.deleted event: {e}")
            return False
        
    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            event_type = message.get('event_type')
            
            logger.info(f"📨 Received event: {event_type}")
            
            # Route to appropriate handler
            if event_type == 'shop.approved':
                success = self.handle_shop_approved(message)
            elif event_type == 'shop.deleted':  # ← ADDED THIS
                success = self.handle_shop_deleted(message)
            else:
                logger.warning(f"⚠️ Unknown event type: {event_type}")
                success = True  # Ack unknown events
            
            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
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
                
                # Bind to shop.approved events
                channel.queue_bind(
                    exchange='shop_events',
                    queue=queue_name,
                    routing_key='shop.approved'
                )
                
                # ✅ ADDED: Bind to shop.deleted events
                channel.queue_bind(
                    exchange='shop_events',
                    queue=queue_name,
                    routing_key='shop.deleted'
                )
                
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self.callback
                )
                
                logger.info("🎧 User service listening for shop events (shop.approved, shop.deleted)…")
                channel.start_consuming()
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping consumer…")
                break
            except Exception as e:
                logger.error(f"❌ Connection error: {e}")
                logger.info("⏳ Retrying in 5 seconds...")
                time.sleep(5)


if __name__ == '__main__':
    consumer = ShopEventConsumer()
    consumer.start_consuming()