#!/usr/bin/env python3
"""
Standalone RabbitMQ Consumer for Wishlist Service
This script runs as a separate service to consume events from RabbitMQ
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main consumer function"""
    logger.info("🚀 Starting Wishlist Consumer Service...")
    
    # Import after path setup
    from app.rabbitmq.connection import rabbitmq_connection
    from app.rabbitmq.consumer import event_consumer
    from app.database import create_db_and_tables
    
    # Initialize database
    try:
        create_db_and_tables()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        return
    
    # Connect to RabbitMQ
    try:
        await rabbitmq_connection.connect()
        logger.info("✅ RabbitMQ connection established")
    except Exception as e:
        logger.error(f"❌ Failed to connect to RabbitMQ: {str(e)}")
        return
    
    # Start consuming messages
    try:
        logger.info("📨 Starting to consume messages...")
        await event_consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("🛑 Consumer interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error in consumer: {str(e)}")
    finally:
        # Cleanup
        try:
            await rabbitmq_connection.close()
            logger.info("✅ RabbitMQ connection closed gracefully")
        except Exception as e:
            logger.error(f"❌ Error closing RabbitMQ connection: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Consumer service stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        sys.exit(1)

