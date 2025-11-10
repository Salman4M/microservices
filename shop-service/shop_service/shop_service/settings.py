from pathlib import Path
from dotenv import load_dotenv

import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv() 

# Service URLs for inter-service communication
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:8006')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "shop.localhost",
    "localhost",
    "127.0.0.1",
    "shop-service-814454543179.europe-west1.run.app",
    "shop-service-web-1",
    'web',
    'web:8000',
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:8002",
    "http://localhost:8007",
    "http://localhost:8007",
    "http://127.0.0.1:8000",
    "https://shop-service-814454543179.europe-west1.run.app",
    "https://api-gateway-service-814454543179.europe-west1.run.app/"
]

# # Cors settings
# CORS_ALLOW_ALL_ORIGINS = True


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    # Apps
    'shops.apps.ShopsConfig'
]

MIDDLEWARE = [
    # 'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shop_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'shop_service.wsgi.application'


# Database(PostgreSQL) configuration

# Check if running on Cloud Run
is_cloud_run = os.environ.get("RUNNING_ON_CLOUDRUN", "").lower() == "true"

if is_cloud_run:
    # Cloud Run configuration with Cloud SQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB'),
            'USER': os.environ.get('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': f"/cloudsql/{os.environ.get('CLOUD_SQL_CONNECTION_NAME')}",
            'PORT': '',
        }
    }
else:
    # Local development configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB'),
            'USER': os.getenv('POSTGRES_USER'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'HOST': os.getenv('POSTGRES_HOST'),
            'PORT': os.getenv('POSTGRES_PORT'),
            'CONN_MAX_AGE': 600,  
            'OPTIONS': {
                'sslmode': 'disable',
            },
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Media / Static configuration

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'shop_service/media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# ============================================
# Update Django Settings
# ============================================
# File: shop-service/shop_service/settings.py

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Change from GatewayHeaderAuthentication to TraefikHeaderAuthentication
        'shop_service.authentication.TraefikHeaderAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# # RestFramework settings
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'shop_service.authentication.GatewayHeaderAuthentication',
#     ),
#     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
# }

# Swagger settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Shop Service API',
    'DESCRIPTION': """
        Shop Service documentation
        
        This API provides endpoints for managing shops, branches, comments, media, and social media.
    """,
    'VERSION': '0.1',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'TAGS': [
        {'name': 'Shop', 'description': 'Shop management endpoints'},
        {'name': 'ShopBranch', 'description': 'Shop branch management endpoints'},
        {'name': 'ShopComment', 'description': 'Shop comment endpoints'},
        {'name': 'ShopMedia', 'description': 'Shop media management endpoints'},
        {'name': 'ShopSocialMedia', 'description': 'Shop social media management endpoints'},
    ],
}

# Logging settings
LOGGING_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGGING_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'formatters': {
        'default': {'format': '{levelname} {asctime} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'file': {'class': 'logging.FileHandler', 'filename': os.path.join(LOGGING_DIR, 'drf_api.log'), 'formatter': 'default'},
        'console': {'class': 'logging.StreamHandler', 'formatter': 'default'},
    },
    'loggers': {
        'django': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': True},
        'shop_service': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': False},
    },
}