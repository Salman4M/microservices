#!/usr/bin/env sh
set -e

echo "Starting FastAPI entrypoint..."

# Local development path
echo "Running locally..."

# Postgres connection settings from .env
POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER}"
POSTGRES_DB="${POSTGRES_DB}"

# Wait for Postgres
for i in $(seq 1 30); do
  if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
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
PORT="${WEB_PORT:-8000}"
echo "Starting uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
