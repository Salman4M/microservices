import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
 
DATABASE_URL = os.getenv("DATABASE_URL")

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# Application Configuration
PROJECT_NAME = "Wishlist Service"
API_V1_STR = "/api/v1"