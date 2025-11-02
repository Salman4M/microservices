#!/usr/bin/env sh
set -e

echo "Starting entrypoint..."

# Determine if running on Cloud Run
if [ "$RUNNING_ON_CLOUDRUN" = "true" ]; then
  echo "Detected Cloud Run environment. Using Cloud SQL socket..."
  export POSTGRES_HOST="/cloudsql/${CLOUD_SQL_CONNECTION_NAME}"
else
  echo "Local environment detected. Using standard host..."
fi

# Wait for Postgres
if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
  for i in $(seq 1 30); do
    if pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
      echo "Postgres is ready!"
      break
    fi
    echo "Postgres not ready yet, retry $i/30"
    sleep 2
  done
  if ! pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
    echo "ERROR: Postgres never became ready. Exiting."
    exit 1
  fi
fi

# Apply migrations
echo "Running migrations..."
python manage.py migrate --noinput || { echo "Migration failed!"; exit 1; }

# Create superuser if not exists
echo "Checking for superuser..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin','admin@example.com','admin') if not User.objects.filter(username='admin').exists() else None"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || { echo "Collectstatic failed!"; exit 1; }

# Start Gunicorn
echo "Starting Gunicorn on 0.0.0.0:$PORT"
exec gunicorn shop_service.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -
