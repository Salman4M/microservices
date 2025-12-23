import logging
from typing import Optional
from aio_pika import Message, DeliveryMode

from app.rabbitmq.connection import rabbitmq_connection
from app.rabbitmq.schemas import WishlistCreatedEvent, WishlistDeletedEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    
    async def publish_wishlist_created(
        self,
        wishlist_id: int,
        user_id: str,
        product_variation_id: Optional[str] = None,
        shop_id: Optional[str] = None,
    ) -> None:
  
        try:
            event = WishlistCreatedEvent(
                wishlist_id=wishlist_id,
                user_id=user_id,
                product_variation_id=product_variation_id,
                shop_id=shop_id,
                metadata={"source": "wishlist_service"}
            )
            
            message_body = event.model_dump_json()
            
            message = Message(
                body=message_body.encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                headers={
                    "event_type": "wishlist.created",
                    "source": "wishlist_service"
                }
            )
            
            if rabbitmq_connection.wishlist_exchange:
                await rabbitmq_connection.wishlist_exchange.publish(
                    message=message,
                    routing_key="wishlist.created"
                )
                logger.info(f"Published wishlist.created event for wishlist_id={wishlist_id}")
            else:
                logger.error("Wishlist exchange is not initialized")
                
        except Exception as e:
            logger.error(f"Failed to publish wishlist.created event: {str(e)}")
    
    async def publish_wishlist_deleted(
        self,
        wishlist_id: int,
        user_id: str,
    ) -> None:

        try:
            event = WishlistDeletedEvent(
                wishlist_id=wishlist_id,
                user_id=user_id,
                metadata={"source": "wishlist_service"}
            )
            
            message_body = event.model_dump_json()
            
            message = Message(
                body=message_body.encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                headers={
                    "event_type": "wishlist.deleted",
                    "source": "wishlist_service"
                }
            )
            
            if rabbitmq_connection.wishlist_exchange:
                await rabbitmq_connection.wishlist_exchange.publish(
                    message=message,
                    routing_key="wishlist.deleted"
                )
                logger.info(f"Published wishlist.deleted event for wishlist_id={wishlist_id}")
            else:
                logger.error("Wishlist exchange is not initialized")
                
        except Exception as e:
            logger.error(f"Failed to publish wishlist.deleted event: {str(e)}")


# Global publisher instance
event_publisher = EventPublisher()