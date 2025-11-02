#!/usr/bin/env sh
set -e

echo "Starting FastAPI entrypoint..."

# Check if running on Cloud Run
if [ -n "$K_SERVICE" ]; then
  echo "Running on Cloud Run..."
  
  # SKIP MIGRATIONS - Run them separately via Cloud Run Jobs
  # This ensures the container starts quickly and passes health checks
  
  echo "Starting uvicorn on port ${PORT:-8000}..."
  exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers
else
  # Local development path
  echo "Running locally..."
  
  if [ -n "$CLOUD_SQL_CONNECTION_NAME" ]; then
    POSTGRES_HOST="/cloudsql/$CLOUD_SQL_CONNECTION_NAME"
  else
    POSTGRES_HOST="${DB_HOST:-db}"
  fi

  # Wait for Postgres
  for i in $(seq 1 30); do
    if pg_isready -h "$POSTGRES_HOST" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}"; then
      echo "Postgres is ready!"
      break
    fi
    echo "Waiting for Postgres... ($i/30)"
    sleep 2
  done

  # Run migrations locally
  echo "Running migrations..."
  alembic upgrade head || { echo "Migration failed!"; exit 1; }

  # Start FastAPI
  exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
fi