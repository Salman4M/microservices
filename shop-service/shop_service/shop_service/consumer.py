import pika
import json
import os
import logging
import django
from django.db import transaction
from dotenv import load_dotenv

# Load environment variables before Django setup
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_service.settings')
django.setup()

from shops.models import ShopOrderItem, Shop

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('shop_service')


class OrderItemConsumer:
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST')
        self.port = int(os.getenv('RABBITMQ_PORT'))
        self.user = os.getenv('RABBITMQ_USER')
        self.password = os.getenv('RABBITMQ_PASS')
        self.connection = None
        self.channel = None
        
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
    
    def handle_order_item_created(self, ch, method, properties, body):
        """Handle order.item.created event"""
        try:
            message = json.loads(body)
            event_type = message.get('event_type')
            
            if event_type != 'order.item.created':
                logger.warning(f"Unknown event type: {event_type}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            shop_id = message.get('shop_id')
            if not shop_id:
                logger.warning("Order item message missing shop_id, skipping")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Check if shop exists
            try:
                shop = Shop.objects.get(id=shop_id)
            except Shop.DoesNotExist:
                logger.warning(f"Shop with id {shop_id} not found, skipping order item")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            order_item_id = message.get('order_item_id')
            if not order_item_id:
                logger.warning("Order item message missing order_item_id, skipping")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Check if order item already exists
            if ShopOrderItem.objects.filter(id=order_item_id).exists():
                logger.info(f"Order item {order_item_id} already exists, skipping")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Create shop order item
            with transaction.atomic():
                shop_order_item = ShopOrderItem.objects.create(
                    id=order_item_id,
                    shop=shop,
                    order_id=message.get('order_id'),
                    product_id=message.get('product_id'),
                    product_variation=message.get('product_variation', ''),
                    quantity=message.get('quantity', 1),
                    price=message.get('price', 0),
                    status=message.get('status', ShopOrderItem.Status.PROCESSING),
                    user_id=message.get('user_id', ''),
                )
                logger.info(f"Created shop order item {shop_order_item.id} for shop {shop_id}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing order item message: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        try:
            self.connection = self.get_connection()
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange='order_events',
                exchange_type='topic',
                durable=True
            )
            
            # Declare queue
            queue_name = 'shop_order_items_queue'
            result = self.channel.queue_declare(
                queue=queue_name,
                durable=True
            )
            
            # Bind queue to exchange
            self.channel.queue_bind(
                exchange='order_events',
                queue=queue_name,
                routing_key='order.item.created'
            )
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=10)
            
            # Start consuming
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self.handle_order_item_created
            )
            
            logger.info(f"Started consuming order items from queue: {queue_name}")
            logger.info("Waiting for messages. To exit press CTRL+C")
            
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            if self.channel:
                self.channel.stop_consuming()
            if self.connection:
                self.connection.close()
        except Exception as e:
            logger.error(f"Error in consumer: {e}", exc_info=True)
            if self.connection:
                self.connection.close()
            raise


if __name__ == '__main__':
    consumer = OrderItemConsumer()
    consumer.start_consuming()
