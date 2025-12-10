import json
import logging
from aio_pika import IncomingMessage
from sqlmodel import Session, select

from app.rabbitmq.connection import rabbitmq_connection
from app.rabbitmq.schemas import UserCreatedEvent, ShopApprovedEvent
from app.database import engine
from app.models import Wishlist, WishlistItem

logger = logging.getLogger(__name__)


class EventConsumer:
    
    async def start_consuming(self) -> None:
        """Start consuming events from RabbitMQ"""
        logger.info("Starting to consume events...")
        
        if not rabbitmq_connection.user_events_queue:
            logger.error("User events queue is not initialized")
            return
        
        try:
            async with rabbitmq_connection.user_events_queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self._process_event(message)
                    
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
    
    async def _process_event(self, message: IncomingMessage) -> None:
        """Process incoming events (user.created or shop.approved)"""
        async with message.process():
            try:
                message_body = json.loads(message.body.decode())
                logger.info(f"Received message: {message_body}")
                
                event_type = message_body.get('event_type')
                
                if event_type == 'user.created':
                    await self._handle_user_created(message_body)
                elif event_type == 'shop.approved':
                    await self._handle_shop_approved(message_body)
                else:
                    logger.warning(f"⚠️ Unknown event type: {event_type}")
                
                logger.info(f"✅ Message processed successfully")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to decode message: {str(e)}")
            except Exception as e:
                logger.error(f"❌ Failed to process message: {str(e)}")
                raise
    
    async def _handle_user_created(self, message_body: dict) -> None:
        """Handle user.created event - Create wishlist for new user"""
        try:
            event = UserCreatedEvent(**message_body)
            logger.info(
                f"Validated user.created event: "
                f"user_uuid={event.user_uuid}, "
                f"email={event.email}, "
                f"is_active={event.is_active}"
            )
            
            # Create wishlist for new user (only if active)
            if event.is_active:
                await self._create_user_wishlist(event.user_uuid)
            else:
                logger.info(f"ℹ️ Skipping wishlist creation for inactive user {event.user_uuid}")
            
        except Exception as e:
            logger.error(f"Failed to handle user.created event: {str(e)}")
            raise
    
    async def _create_user_wishlist(self, user_uuid: str) -> None:
        """Create wishlist for a new user"""
        try:
            with Session(engine) as session:
                # Check if wishlist already exists
                existing = session.exec(
                    select(Wishlist).where(Wishlist.user_id == user_uuid)
                ).first()
                
                if existing:
                    logger.info(f"ℹ️ Wishlist already exists for user {user_uuid}")
                    return
                
                # Create new wishlist
                wishlist = Wishlist(user_id=user_uuid)
                session.add(wishlist)
                session.commit()
                session.refresh(wishlist)
                
                logger.info(f"✅ Created wishlist {wishlist.id} for user {user_uuid}")
                
        except Exception as e:
            logger.error(f"Failed to create wishlist for user {user_uuid}: {str(e)}")
            raise
    
    async def _handle_shop_approved(self, message_body: dict) -> None:
        """
        Handle shop.approved event.
        When a user becomes a shop owner, delete their wishlist.
        Shop owners don't need wishlists - they sell products, not buy them.
        """
        try:
            event = ShopApprovedEvent(**message_body)
            logger.info(
                f"📨 Processing shop.approved event: "
                f"user_uuid={event.user_uuid}, "
                f"shop_id={event.shop_id}"
            )
            
            await self._delete_user_wishlist(event.user_uuid)
            
        except Exception as e:
            logger.error(f"Failed to handle shop.approved event: {str(e)}")
            raise
    
    async def _delete_user_wishlist(self, user_uuid: str) -> None:
        """
        Delete entire wishlist and all items for a user.
        Used when user becomes a shop owner.
        """
        try:
            with Session(engine) as session:
                # Find user's wishlist
                wishlist = session.exec(
                    select(Wishlist).where(Wishlist.user_id == user_uuid)
                ).first()
                
                if not wishlist:
                    logger.info(
                        f"ℹ️ No wishlist found for user {user_uuid} - nothing to delete"
                    )
                    return
                
                # Count items before deletion
                items = session.exec(
                    select(WishlistItem).where(WishlistItem.wishlist_id == wishlist.id)
                ).all()
                
                items_count = len(items)
                
                # Delete wishlist (cascade will delete items)
                session.delete(wishlist)
                session.commit()
                
                logger.info(
                    f"✅ Deleted wishlist (ID: {wishlist.id}) with {items_count} items "
                    f"for new shop owner {user_uuid}"
                )
                
        except Exception as e:
            logger.error(f"Failed to delete wishlist for user {user_uuid}: {str(e)}")
            raise


event_consumer = EventConsumer()