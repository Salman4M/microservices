import os
import sys
import json
import time
import asyncio
from pathlib import Path
import logging
import aio_pika
from elasticsearch import Elasticsearch

from elastic.models import ShopSchema, ProductSchema


logger = logging.getLogger("consumer")


ELASTIC_HOST = os.getenv('ELASTIC_HOST', 'http://elasticsearch:9200')
ELASTIC_USERNAME = os.getenv('ELASTIC_USERNAME', 'elastic')
ELASTIC_PASSWORD = os.getenv('ELASTIC_PASSWORD', '')

es = Elasticsearch(
    [ELASTIC_HOST],
    basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD) if ELASTIC_PASSWORD else None,
    verify_certs=False,
    ssl_show_warn=False,
    request_timeout=30  # Increased timeout for slow connections
)

SHOP_INDEX_NAME = "shops"
PRODUCT_INDEX_NAME = "products"


def wait_for_elasticsearch(max_retries=30, delay=2):
    for i in range(max_retries):
        try:
            if es.ping():
                logger.info("Elasticsearch is available.")
                return True
        except Exception as e:
            logger.warning(f"Elasticsearch not ready: {e}")
        time.sleep(delay)
    logger.error("Elasticsearch is not available after retries.")
    return False

def wait_for_rabbitmq(max_retries=30, delay=2):
    rabbit_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    rabbit_port = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbit_user = os.getenv("RABBITMQ_USER", "guest")
    rabbit_pass = os.getenv("RABBITMQ_PASS", "guest")

    import pika
    for i in range(max_retries):
        try:
            credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
            parameters = pika.ConnectionParameters(
                host=rabbit_host,
                port=rabbit_port,
                credentials=credentials,
                connection_attempts=1,
                retry_delay=1
            )
            connection = pika.BlockingConnection(parameters)
            connection.close()
            logger.info("RabbitMQ is available.")
            return True
        except Exception as e:
            logger.warning(f"RabbitMQ not ready: {e}")
            time.sleep(delay)
    logger.error("RabbitMQ is not available after retries.")
    return False

async def start_consumer():
    rabbit_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    rabbit_port = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbit_user = os.getenv("RABBITMQ_USER", "guest")
    rabbit_pass = os.getenv("RABBITMQ_PASS", "guest")
    rabbit_url = f"amqp://{rabbit_user}:{rabbit_pass}@{rabbit_host}:{rabbit_port}/"

    logger.info("Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(rabbit_url)
    channel = await connection.channel()
    
    # Declare exchanges
    shop_exchange = await channel.declare_exchange("shop_events", aio_pika.ExchangeType.TOPIC, durable=True)
    product_exchange = await channel.declare_exchange("product_events", aio_pika.ExchangeType.TOPIC, durable=True)
    
    # Declare queues
    shop_queue = await channel.declare_queue("shop_queue", durable=True)
    product_queue = await channel.declare_queue("product_queue", durable=True)
    
    # Bind queues to exchanges
    await shop_queue.bind(shop_exchange, routing_key="shop.*")
    await product_queue.bind(product_exchange, routing_key="product.*")

    logger.info("RabbitMQ consumer started. Waiting for messages...")

    async def process_shop_message(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body)
                event_type = data.get("event_type")
                shop_data = data.get("shop_data", {})
                shop_id = data.get("shop_id")

                if event_type == "deleted":
                    es.delete(index=SHOP_INDEX_NAME, id=shop_id, ignore=[404])
                    logger.info(f"Deleted shop {shop_id} from Elasticsearch")
                else:
                    shop = ShopSchema(**shop_data)
                    es.index(index=SHOP_INDEX_NAME, id=shop_id, document=shop.model_dump())
                    logger.info(f"Indexed shop {shop_id} ({shop.name}) to Elasticsearch")
            except Exception as e:
                logger.error(f"Failed processing shop message: {e}", exc_info=True)

    async def process_product_message(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body)
                event_type = data.get("event_type")
                product_id = data.get("product_id")
                
                if event_type == "product.created" or event_type == "product.updated":
                    product_data = data.get("product_data", {})
                    product = ProductSchema(**product_data)
                    es.index(index=PRODUCT_INDEX_NAME, id=product_id, document=product.model_dump())
                    logger.info(f"Indexed product {product_id} ({product.title}) to Elasticsearch")
                elif event_type == "product.deleted":
                    es.delete(index=PRODUCT_INDEX_NAME, id=product_id, ignore=[404])
                    logger.info(f"Deleted product {product_id} from Elasticsearch")
            except Exception as e:
                logger.error(f"Failed processing product message: {e}", exc_info=True)

    # Start consuming from all queues concurrently
    async def consume_shop():
        async with shop_queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_shop_message(message)
    
    async def consume_product():
        async with product_queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_product_message(message)
    
    logger.info("All queues are being consumed. Waiting for messages...")
    
    # Run all consumers concurrently
    await asyncio.gather(
        consume_shop(),
        consume_product()
    )

def main():
    if not wait_for_elasticsearch():
        sys.exit(1)
    if not wait_for_rabbitmq():
        sys.exit(1)
    
    # Create indices before starting consumer
    try:
        from elastic.documents import create_indices
        create_indices()
        logger.info("Elasticsearch indices created or already exist")
    except Exception as e:
        logger.warning(f"Could not create indices: {e}")

    try:
        logger.info("Starting consumer...")
        asyncio.run(start_consumer())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()