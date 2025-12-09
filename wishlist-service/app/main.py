from fastapi import FastAPI
import asyncio
import logging

from app.database import create_db_and_tables
from app.config import PROJECT_NAME, API_V1_STR
from app.api.v1.endpoints import wishlist

from app.rabbitmq.connection import rabbitmq_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=PROJECT_NAME,
    description="Wishlist Microservice for E-commerce Platform",
    version="1.0.0",
)

# Include routers
app.include_router(wishlist.router, prefix=API_V1_STR)


@app.on_event("startup")
async def startup_event():
 
    logger.info("Starting Wishlist Service...")

    # create_db_and_tables()
    logger.info("Database tables created")

    # Note: Consumer runs as a separate service, no need to start it here
    try:
        await rabbitmq_connection.connect()
        logger.info("RabbitMQ connected (for publishing only)")
    except Exception as e:
        logger.warning(f"Failed to connect to RabbitMQ: {str(e)} (consumer will handle this)")


@app.on_event("shutdown")
async def shutdown_event():

    logger.info("Shutting down Wishlist Service...")
    
    try:
        await rabbitmq_connection.close()
        logger.info("RabbitMQ connection closed gracefully")
    except Exception as e:
        logger.error(f"Error closing RabbitMQ: {str(e)}")


@app.get("/")
def root():
    return {
        "message": "Wishlist Service is running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health_check():
   
    rabbitmq_status = "connected" if rabbitmq_connection.connection else "disconnected"
    
    return {
        "status": "healthy",
        "service": "wishlist",
        "rabbitmq": rabbitmq_status
    }