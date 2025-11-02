import pika
import json
import os
import time
from sqlalchemy.orm import Session
from . import crud, models
from .core.db import SessionLocal


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
    
    def handle_user_created(self, db: Session, message: dict):
        try:
            user_uuid = message.get('user_uuid')
            if not user_uuid:
                print(f"⚠️ Missing user_uuid in message")
                return False
            
            cart = crud.create_cart(db, user_uuid)
            print(f"✅ Created cart {cart.id} for user {user_uuid}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create cart: {e}")
            return False
    
    def handle_order_created(self, db: Session, message: dict):
        try:
            data = message.get('data', {})
            user_uuid = data.get('user_uuid')
            cart_id = data.get('cart_id')
            order_id = data.get('order_id')
            
            if not all([user_uuid, cart_id]):
                print(f"⚠️ Missing required fields in order.created event")
                return False
            
            # Find the cart
            cart = db.query(models.ShopCart).filter(
                models.ShopCart.user_uuid == user_uuid,
                models.ShopCart.id == cart_id
            ).first()
            
            if not cart:
                print(f"⚠️ Cart {cart_id} not found for user {user_uuid}")
                return False
            
            # Delete all items from cart
            deleted_count = db.query(models.CartItem).filter(
                models.CartItem.shop_cart_id == cart_id
            ).delete()
            
            db.commit()
            print(f"✅ Cleared {deleted_count} items from cart {cart_id} after order {order_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to clear cart: {e}")
            db.rollback()
            return False
        

    def handle_shop_created(self, db: Session, message: dict):
        """
        Handle shop.created event.
        When user becomes a shop owner, delete their shopping cart.
        Sellers don't buy - they sell!
        """
        try:
            user_uuid = message.get('user_uuid')
            shop_id = message.get('shop_id')
            
            if not user_uuid:
                print(f"⚠️ Missing user_uuid in shop.created event")
                return False
            
            # Use the dedicated CRUD function to delete cart
            deleted = crud.delete_cart_for_user(db, user_uuid)
            
            if deleted:
                print(f"✅ Deleted cart for new shop owner {user_uuid} (shop: {shop_id})")
            else:
                print(f"ℹ️ No cart found for user {user_uuid} - nothing to delete")
            
            return True
                
        except Exception as e:
            print(f"❌ Failed to handle shop.created event: {e}")
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
            
            print(f"📨 Received event: {event_type}")
            
            # Route to appropriate handler
            if event_type == 'user.created':
                if message.get('is_active', True):  # Only create cart for active users
                    success = self.handle_user_created(db, message)
                else:
                    print(f"ℹ️ Skipping inactive user")
                    success = True
                    
            elif event_type == 'order.created':
                success = self.handle_order_created(db, message)

            elif event_type == 'shop.created':
                success = self.handle_shop_created(db, message)
                
            else:
                print(f"⚠️ Unknown event type: {event_type}")
                success = True  # Ack unknown events to avoid blocking
            
            # Acknowledge or reject message
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
        finally:
            db.close()
    
    def start_consuming(self):
        while True:
            try:
                connection = self.get_connection()
                channel = connection.channel()
                
                # Declare exchanges
                channel.exchange_declare(
                    exchange='user_events',
                    exchange_type='topic',
                    durable=True
                )
                
                channel.exchange_declare(
                    exchange='order_events',
                    exchange_type='topic',
                    durable=True
                )

                channel.exchange_declare(
                    exchange='shop_events',
                    exchange_type='topic',
                    durable=True
                )
                
                # Declare queue
                queue_name = 'shopcart_events'
                channel.queue_declare(
                    queue=queue_name,
                    durable=True
                )
                
                # Bind queue to user events
                channel.queue_bind(
                    exchange='user_events',
                    queue=queue_name,
                    routing_key='user.created'
                )
                
                # Bind queue to order events
                channel.queue_bind(
                    exchange='order_events',
                    queue=queue_name,
                    routing_key='order.created'
                )
                # Bind queue to shop events
                channel.queue_bind(
                    exchange='shop_events',
                    queue=queue_name,
                    routing_key='shop.created'
                )
                
                channel.basic_qos(prefetch_count=1)
                
                # Start consuming
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self.callback
                )
                
                print('🎧 Waiting for messages (user.created, order.created, shop.created). To exit press CTRL+C')
                channel.start_consuming()
                
            except KeyboardInterrupt:
                print("🛑 Stopping consumer...")
                break
            except Exception as e:
                print(f"❌ Connection error: {e}")
                print("⏳ Retrying in 5 seconds...")
                time.sleep(5)


def start_consumer():
    """Entry point for consumer"""
    consumer = RabbitMQConsumer()
    consumer.start_consuming()