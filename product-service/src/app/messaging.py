import pika
import json
import os
import time
from sqlalchemy.orm import Session
from src.app.core.db import SessionLocal
from src.app.models.v1.product_variation import ProductVariation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQConsumer:
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
    
    def handle_order_created(self, db: Session, message: dict):
      
        try:
            data = message.get('data', {})
            items = data.get('items', [])
            order_id = data.get('order_id')
            
            if not items:
                logger.warning(f"⚠️ No items in order.created event for order {order_id}")
                return True  # ✅ Return True - shopcart events don't have items
            
            logger.info(f"📦 Processing order {order_id} with {len(items)} items")
            
            updated_count = 0
            error_count = 0
            
            for item in items:
                variation_id = item.get('product_variation_id')
                quantity = item.get('quantity', 0)
                
                if not variation_id or quantity <= 0:
                    logger.warning(f"⚠️ Invalid item data: {item}")
                    continue
                
                # Find the product variation
                variation = db.query(ProductVariation).filter(
                    ProductVariation.id == variation_id
                ).first()
                
                if not variation:
                    logger.error(f"❌ Product variation {variation_id} not found")
                    error_count += 1
                    continue
                
                # Check if enough stock
                if variation.amount < quantity:
                    logger.error(
                        f"❌ Insufficient stock for {variation_id}: "
                        f"requested {quantity}, available {variation.amount}"
                    )
                    error_count += 1
                    # Continue anyway - order already created
                    continue
                
                # Reduce stock
                old_amount = variation.amount
                variation.amount -= quantity
                updated_count += 1
                
                logger.info(
                    f"✅ Reduced stock for variation {variation_id}: "
                    f"{old_amount} → {variation.amount} (sold {quantity})"
                )
            
            db.commit()
            logger.info(
                f"✅ Successfully processed order {order_id}: "
                f"{updated_count} variations updated, {error_count} errors"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process order.created: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False
    
    def callback(self, ch, method, properties, body):
        """Handle incoming messages from RabbitMQ"""
        db: Session = SessionLocal()
        success = False
        
        try:
            message = json.loads(body)
            event_type = message.get('event_type') or message.get('event')
            
            logger.info(f"📨 Received event: {event_type}")
            
            # Route to appropriate handler
            if event_type == 'order.created':
                success = self.handle_order_created(db, message)
            else:
                logger.warning(f"⚠️ Unknown event type: {event_type}")
                success = True  # Ack unknown events
            
            # Acknowledge or reject message
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
        finally:
            db.close()
    
    def start_consuming(self):
        while True:
            try:
                connection = self.get_connection()
                channel = connection.channel()
                
                # Declare order events exchange
                channel.exchange_declare(
                    exchange='order_events',
                    exchange_type='topic',
                    durable=True
                )
                
                # Declare queue for product service
                queue_name = 'product_events'
                channel.queue_declare(
                    queue=queue_name,
                    durable=True
                )
                
                # Bind queue to order.created events
                channel.queue_bind(
                    exchange='order_events',
                    queue=queue_name,
                    routing_key='order.created'
                )
                
                channel.basic_qos(prefetch_count=1)
                
                # Start consuming
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self.callback
                )
                
                logger.info('🎧 Product Service waiting for order.created events. Press CTRL+C to exit')
                channel.start_consuming()
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping consumer...")
                break
            except Exception as e:
                logger.error(f"❌ Connection error: {e}")
                logger.info("⏳ Retrying in 5 seconds...")
                time.sleep(5)


def start_consumer():
    """Entry point for consumer"""
    consumer = RabbitMQConsumer()
    consumer.start_consuming()