#!/usr/bin/env sh
set -e

echo "=== Starting entrypoint ==="

# --- DB host təyini ---
export DB_HOST=${DB_HOST:-db}
export DB_USER=${DB_USER:-ecommerce_user}
export DB_NAME=${DB_NAME:-ecommerce_db}
export DB_PASSWORD=${DB_PASSWORD:-12345}
export DB_PORT=${DB_PORT:-5432}

echo "Using Postgres:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  DB: $DB_NAME"
echo "  User: $DB_USER"

# --- Wait for Postgres ---
echo "Waiting for Postgres to be ready..."
until python -c "
import sys
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host='$DB_HOST',
        port='$DB_PORT',
        user='$DB_USER',
        password='$DB_PASSWORD',
        database='$DB_NAME',
        connect_timeout=5
    )
    conn.close()
    sys.exit(0)
except psycopg2.OperationalError as e:
    sys.exit(1)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Postgres is up - continuing..."

# --- Django Migrate ---
echo "Running Django migrations..."
python manage.py migrate --noinput

# --- Static files toplamaq ---
echo "Collecting static files..."
python manage.py collectstatic --noinput

# --- Superuser yaratmaq (non-interactive) ---
echo "Creating superuser if not exists..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'ilham'
email = 'ilham@example.com'
password = 'ecommerce'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
"

# --- Gunicorn serverini işə sal ---
echo "Starting Gunicorn on 0.0.0.0:${PORT:-8000}..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 2 \
    --timeout 0 \
    --access-logfile - \
    --error-logfile -
