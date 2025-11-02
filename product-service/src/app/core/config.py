import os
from dotenv import load_dotenv

load_dotenv()

# Service URLs for inter-service communication
SHOP_SERVICE_URL = os.getenv('SHOP_SERVICE_URL', 'http://localhost:8007')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:UniversityDB2025@db:5432/ECommerce_Product_DB')

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG_FILE = os.getenv('LOG_FILE', 'logs/product_service.log')

