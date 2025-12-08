import json
import logging
from aio_pika import IncomingMessage
from sqlmodel import Session

from app.rabbitmq.connection import rabbitmq_connection
from app.rabbitmq.schemas import UserCreatedEvent
from app.database import engine
from app.models import Wishlist

logger = logging.getLogger(__name__)


class EventConsumer:
    
    async def start_consuming(self) -> None:

        logger.info("Starting to consume user events...")
        
        if not rabbitmq_connection.user_events_queue:
            logger.error("User events queue is not initialized")
            return
        
        try:
            async with rabbitmq_connection.user_events_queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self._process_user_created_event(message) # type: ignore
                    
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
    
    async def _process_user_created_event(self, message: IncomingMessage) -> None: 

        async with message.process():
            try:
                message_body = json.loads(message.body.decode())
                logger.info(f"Received message: {message_body}")
                
                # Validate and parse event
                event = UserCreatedEvent(**message_body)
                logger.info(f"Validated event: user_uuid={event.user_uuid}, email={event.email}, is_active={event.is_active}")
                
                await self._create_user_wishlist_entry(event)
  
                logger.info(f"✅ Message processed successfully for user_uuid={event.user_uuid}")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to decode message: {str(e)}")
                # Don't re-raise to avoid message requeue
                
            except Exception as e:
                logger.error(f"❌ Failed to process message: {str(e)}")
                # Re-raise to requeue message if needed
                raise
    
    async def _create_user_wishlist_entry(self, event: UserCreatedEvent) -> None:
 
        try:
            with Session(engine) as session:
                
                logger.info(f"User wishlist ready for user_uuid={event.user_uuid}")
                
        except Exception as e:
            logger.error(f"Failed to create wishlist entry: {str(e)}")
            raise

event_consumer = EventConsumer()