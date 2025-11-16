import pika
import json
import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('order_service')


class RabbitMQPublisher:
    """
    Singleton RabbitMQ publisher with connection reuse.
    Keeps connection open to avoid reconnection overhead.
    """
    _instance: Optional['RabbitMQPublisher'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.user = os.getenv('RABBITMQ_USER', 'admin')
        self.password = os.getenv('RABBITMQ_PASS', 'admin12345')
        
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._initialized = True
        
        # Connect immediately
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                return  # Already connected
                
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange (idempotent)
            self.channel.exchange_declare(
                exchange='order_events',
                exchange_type='topic',
                durable=True
            )
            
            logger.info("✅ Connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
            raise
    
    def _ensure_connection(self):
        """Ensure connection is alive, reconnect if needed"""
        try:
            if not self.connection or self.connection.is_closed:
                logger.warning("⚠️ Connection lost, reconnecting...")
                self._connect()
            elif not self.channel or self.channel.is_closed:
                logger.warning("⚠️ Channel closed, recreating...")
                self.channel = self.connection.channel()
                self.channel.exchange_declare(
                    exchange='order_events',
                    exchange_type='topic',
                    durable=True
                )
        except Exception as e:
            logger.error(f"❌ Failed to ensure connection: {e}")
            raise
    
    def publish_order_created(self, order_id: int, user_uuid: str, cart_id: int, items: list = None):

        try:
            self._ensure_connection()
            
            message = {
                'event': 'order.created',
                'event_type': 'order.created',  # Add both for compatibility
                'data': {
                    'order_id': order_id,
                    'user_uuid': str(user_uuid),
                    'cart_id': cart_id,
                    'items': items or [] 
                }
            }
            
            self.channel.basic_publish(
                exchange='order_events',
                routing_key='order.created',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2, 
                    content_type='application/json'
                )
            )
            
            logger.info(f"📤 Published order.created event for order {order_id} with {len(items or [])} items")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish order.created event: {e}")
            # Try to reconnect for next time
            try:
                self._connect()
            except:
                pass
            raise

    def publish_order_items(self, order_id: str, items: list):
        try:
            self._ensure_connection()

            for item in items:
                message = {
                    'event_type': 'order.item_validation',
                    'order_id': str(order_id),
                    'shop_id': str(item['shop_id']),
                    'item_id': str(item['item_id']),
                    'quantity': item['quantity'],
                    'variation_data': item.get('variation_data')
                }

                self.channel.basic_publish(
                    exchange='order_events',
                    routing_key='order.item_variation',
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )

                logger.info(f"published order.item_variation | order={order_id} shop={item['shop_id']} item={item['item_id']}")

            return True

        except Exception as e:
            logger.error(f"failed to publish order.item_variation event: {e}", exc_info=True)
            try:
                self._connect()
            except:
                pass
            return False

    def publish_order_item_created(self, order_item_id: int, order_id: int, shop_id: str, 
                                   product_id: str, product_variation: str, quantity: int, 
                                   price: int, status: int, user_id: str):
        """Publish order.item.created event for shop-service to create ShopOrderItem"""
        try:
            self._ensure_connection()

            message = {
                'event_type': 'order.item.created',
                'order_item_id': str(order_item_id),
                'order_id': str(order_id),
                'shop_id': str(shop_id),
                'product_id': str(product_id),
                'product_variation': str(product_variation),
                'quantity': quantity,
                'price': price,
                'status': status,
                'user_id': str(user_id)
            }

            self.channel.basic_publish(
                exchange='order_events',
                routing_key='order.item.created',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )

            logger.debug(f"Published order.item.created event - OrderItem: {order_item_id}, Shop: {shop_id}, Order: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish order.item.created event: {e}", exc_info=True)
            try:
                self._connect()
            except:
                pass
            return False

    def publish_order_item_status_updated(self, order_item_id: int, order_id: int, shop_id: str, 
                                         status: int):
        """Publish order.item.status.updated event for shop-service to sync ShopOrderItem status"""
        try:
            self._ensure_connection()

            message = {
                'event_type': 'order.item.status.updated',
                'order_item_id': str(order_item_id),
                'order_id': str(order_id),
                'shop_id': str(shop_id),
                'status': status
            }

            self.channel.basic_publish(
                exchange='order_events',
                routing_key='order.item.status.updated',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )

            logger.debug(f"Published order.item.status.updated event - OrderItem: {order_item_id}, Status: {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish order.item.status.updated event: {e}", exc_info=True)
            try:
                self._connect()
            except:
                pass
            return False
    
    def close(self):
        """Close connection (call on shutdown)"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("✅ Closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"⚠️ Error closing connection: {e}")


# Global singleton instance
rabbitmq_producer = RabbitMQPublisher()

# class RabbitMQPublisher:
#     def __init__(self):
#         self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
#         self.port = int(os.getenv('RABBITMQ_PORT', 5672))
#         self.user = os.getenv('RABBITMQ_USER', 'admin')
#         self.password = os.getenv('RABBITMQ_PASS', 'admin12345')
        
#     def get_connection(self):
#         credentials = pika.PlainCredentials(self.user, self.password)
#         parameters = pika.ConnectionParameters(
#             host=self.host,
#             port=self.port,
#             credentials=credentials,
#             heartbeat=600,
#             blocked_connection_timeout=300
#         )
#         return pika.BlockingConnection(parameters)
    
#     def publish_order_items(self, order_id: str, items: list):
#         """
#         Publish 'order.item_variation' event for each item in an order.
#         Example of `items`:
#         [
#             {
#                 "shop_id": "uuid-of-shop",
#                 "item_id": "id-of-item",
#                 "quantity": 3,
#                 "variation_data": {...}
#             },
#             ...
#         ]
#         """
#         try:
#             connection = self.get_connection()
#             channel = connection.channel()
            
#             # Declare exchange (durable so it persists between restarts)
#             channel.exchange_declare(
#                 exchange='order_events',
#                 exchange_type='topic',
#                 durable=True
#             )

#             for item in items:
#                 message = {
#                     'event_type': 'order.item_validation',
#                     'order_id': str(order_id),
#                     'shop_id': str(item['shop_id']),
#                     'item_id': str(item['item_id']),
#                     'quantity': item['quantity'],
#                     'variation_data': item.get('variation_data')
#                 }

#                 channel.basic_publish(
#                     exchange='order_events',
#                     routing_key='order.item_variation',
#                     body=json.dumps(message),
#                     properties=pika.BasicProperties(
#                         delivery_mode=2,
#                         content_type='application/json'
#                     )
#                 )

#                 logger.info(f"published order.item_variation event | order={order_id} shop={item['shop_id']} item={item['item_id']}")
            
#             connection.close()

#         except Exception as e:
#             logger.error(f"failed to publish order.item_variation event: {e}", exc_info=True)


# # Singleton instance
# # producer = RabbitMQPublisher()