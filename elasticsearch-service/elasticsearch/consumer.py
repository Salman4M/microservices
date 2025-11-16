import os
import json
import pika
import aio_pika
from .documents import ELASTIC, INDEX_NAME
from .logging_config import get_logger
from dotenv import load_dotenv

from .models import ShopSchema

load_dotenv('')

logger = get_logger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"


async def start_consumer():
    logger.info("Starting RabbitMQ consumer...")
    logger.info(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        logger.info("Successfully connected to RabbitMQ")
        
        channel = await connection.channel()
        queue = await channel.declare_queue("shop_queue", durable=True)
        logger.info("Queue 'shop_queue' declared successfully")
        logger.info("Listening for messages...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body)
                        event_type = data.get("event_type")
                        shop_data = data.get("shop_data", {})
                        shop_id = data.get("shop_id")

                        if event_type == "deleted":
                            ELASTIC.delete(index=INDEX_NAME, id=shop_id, ignore=[404])
                            logger.info(f"Deleted shop from Elasticsearch: shop_id={shop_id}")
                        else:
                            shop = ShopSchema(**shop_data)
                            ELASTIC.index(index=INDEX_NAME, id=shop_id, document=shop.model_dump())
                            logger.info(f"Indexed shop in Elasticsearch: shop_id={shop_id}, name={shop.name}, event_type={event_type}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message body as JSON: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error in consumer: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import asyncio
    try:
        logger.info("Initializing consumer service...")
        asyncio.run(start_consumer())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise