import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load env
load_dotenv('')

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-this')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# CSRF
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8001', 'http://localhost:8001']

# config/settings.py - ƏLAVƏ EDİN
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:8000')

# Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'analitic',
    'drf_yasg',
    'drf_spectacular',
]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # static fayllar üçün
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ('v1', 'v2'),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}



SPECTACULAR_SETTINGS = {
    'TITLE': 'Analitic API',
    'DESCRIPTION': 'Analitic servisin API endpoint-ləri',
    'VERSION': 'v1',
    'CONTACT': {'email': 'ilham@example.com'},
    'LICENSE': {'name': 'BSD License'},
}






TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Local Windows üçün:
if os.getenv("DOCKER", None) == "1":
    DB_HOST = os.getenv("POSTGRES_HOST", "db")  # Docker Compose konteyner adı (docker-compose.yml-də "db")

else:
    DB_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")  # Lokal host

# config/settings.py - DÜZƏLDİN
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'ecommerce_db'),         # ✅ docker-compose.yml ilə uyğun
        'USER': os.getenv('DB_USER', 'ecommerce_user'),       # ✅ docker-compose.yml ilə uyğun
        'PASSWORD': os.getenv('DB_PASSWORD', '12345'),       # ✅ docker-compose.yml ilə uyğun
        'HOST': DB_HOST,
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging settings
LOGGING_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGGING_DIR, exist_ok=True)

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'django_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'django.log'),
            'formatter': 'default',
        },
        'analitic_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'analitic.log'),
            'formatter': 'default',
        },
        'analitic_service_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'analitic_service.log'),
            'formatter': 'default',
        },
        'analitic_views_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'analitic_views.log'),
            'formatter': 'default',
        },
        'product_client_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'product_client.log'),
            'formatter': 'default',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['django_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'analitic': {
            'handlers': ['analitic_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'analitic.services': {
            'handlers': ['analitic_service_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'analitic.services.analitic_service': {
            'handlers': ['analitic_service_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'analitic.views': {
            'handlers': ['analitic_views_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'analitic.views.order_views': {
            'handlers': ['analitic_views_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'analitic.product_client': {
            'handlers': ['product_client_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}