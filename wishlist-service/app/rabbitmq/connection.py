from aio_pika import connect_robust
from aio_pika.abc import (
    AbstractRobustConnection,
    AbstractRobustChannel,
    AbstractRobustExchange,
    AbstractRobustQueue,
)
from typing import Optional
import logging

from app.rabbitmq.config import rabbitmq_settings

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    
    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        
        # Exchanges
        self.user_exchange: Optional[AbstractRobustExchange] = None
        self.wishlist_exchange: Optional[AbstractRobustExchange] = None
        self.shop_exchange: Optional[AbstractRobustExchange] = None
        
        # Queues
        self.user_events_queue: Optional[AbstractRobustQueue] = None
    
    async def connect(self) -> None:
        """Connect to RabbitMQ and set up exchanges and queues"""
        try:
            logger.info(
                f"Connecting to RabbitMQ: host={rabbitmq_settings.rabbitmq_host}, "
                f"port={rabbitmq_settings.rabbitmq_port}, user={rabbitmq_settings.rabbitmq_user}"
            )
   
            # Build URL from individual parameters
            connection_url = rabbitmq_settings.rabbitmq_url
            self.connection = await connect_robust(
                connection_url,
                timeout=30,
            )
            logger.info("RabbitMQ connection established")
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            logger.info("RabbitMQ channel created")
            
            await self._declare_exchanges()
            await self._declare_queues()
            
            logger.info("RabbitMQ setup completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    async def _declare_exchanges(self) -> None:
        """Declare all required exchanges"""
        if not self.channel:
            raise RuntimeError("Channel is not initialized")
        
        # User events exchange
        self.user_exchange = await self.channel.declare_exchange(
            name=rabbitmq_settings.user_exchange,
            type=rabbitmq_settings.exchange_type,
            durable=rabbitmq_settings.durable,
        )
        logger.info(f"Exchange declared: {rabbitmq_settings.user_exchange}")
        
        # Wishlist events exchange
        self.wishlist_exchange = await self.channel.declare_exchange(
            name=rabbitmq_settings.wishlist_exchange,
            type=rabbitmq_settings.exchange_type,
            durable=rabbitmq_settings.durable,
        )
        logger.info(f"Exchange declared: {rabbitmq_settings.wishlist_exchange}")
        
        # Shop events exchange
        self.shop_exchange = await self.channel.declare_exchange(
            name=rabbitmq_settings.shop_exchange,
            type=rabbitmq_settings.exchange_type,
            durable=rabbitmq_settings.durable,
        )
        logger.info(f"Exchange declared: {rabbitmq_settings.shop_exchange}")
    
    async def _declare_queues(self) -> None:
        """Declare and bind queues"""
        if not self.channel:
            raise RuntimeError("Channel is not initialized")
        
        # Main queue for user and shop events
        self.user_events_queue = await self.channel.declare_queue(
            name=rabbitmq_settings.user_events_queue,
            durable=rabbitmq_settings.durable,
            auto_delete=False,
        )
        logger.info(f"Queue declared: {rabbitmq_settings.user_events_queue}")
        
        # Bind to user.created events
        await self.user_events_queue.bind(
            exchange=self.user_exchange,
            routing_key="user.created"
        )
        logger.info("Queue bound to user.created events")
        
        # Bind to shop.approved events
        await self.user_events_queue.bind(
            exchange=self.shop_exchange,
            routing_key="shop.approved"
        )
        logger.info("Queue bound to shop.approved events")
    
    async def close(self) -> None:
        """Close RabbitMQ connections"""
        if self.channel:
            await self.channel.close()
            logger.info("RabbitMQ channel closed")
        
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")


rabbitmq_connection = RabbitMQConnection()