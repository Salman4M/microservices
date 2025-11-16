import pika
import json
import os
import logging
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger('shop_service')


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
    
    def publish_shop_created(self, user_uuid: str, shop_id: str, shop_data: dict):
        """Publish shop.approved event when a shop status changes to APPROVED"""
        try:
            connection = self.get_connection()
            channel = connection.channel()
            
            channel.exchange_declare(
                exchange='shop_events',
                exchange_type='topic',
                durable=True
            )
            
            message = {
                'event_type': 'shop.approved',
                'user_uuid': str(user_uuid),
                'shop_id': str(shop_id),
                'is_shop_owner': True,
                'shop_data': shop_data
            }
            
            channel.basic_publish(
                exchange='shop_events',
                routing_key='shop.approved',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info(f"published shop.approved event | user={user_uuid} shop={shop_id}")
            connection.close()
          
        except Exception as e:
            logger.error(f"failed to publish shop.approved event: {e}", exc_info=True)

    def _publish(self, event_type: str, user_uuid: str, shop_id: str, shop_data: dict = None):
        """Helper method to publish shop events"""
        try:
            connection = self.get_connection()
            channel = connection.channel()
            
            channel.exchange_declare(
                exchange='shop_events',
                exchange_type='topic',
                durable=True
            )
            
            message = {
                'event_type': f'shop.{event_type}',
                'user_uuid': str(user_uuid),
                'shop_id': str(shop_id),
                'is_shop_owner': True,
            }
            
            if shop_data:
                message['shop_data'] = shop_data
            
            channel.basic_publish(
                exchange='shop_events',
                routing_key=f'shop.{event_type}',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info(f"published shop.{event_type} event | user={user_uuid} shop={shop_id}")
            connection.close()
          
        except Exception as e:
            logger.error(f"failed to publish shop.{event_type} event: {e}", exc_info=True)

    def publish_shop_updated(self, user_uuid: str, shop_id: str, shop_data: dict):
        logger.info(f"published shop.updated event | user={user_uuid} shop={shop_id}")
        self._publish('updated', user_uuid, shop_id, shop_data)

    def publish_shop_deleted(self, user_uuid: str, shop_id: str):
        logger.info(f"published shop.deleted event | user={user_uuid} shop={shop_id}")
        self._publish('deleted', user_uuid, shop_id)


publisher = RabbitMQPublisher()