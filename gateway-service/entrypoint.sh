#!/usr/bin/env sh
set -e

echo "Starting FastAPI entrypoint..."

# Start FastAPI
exec uvicorn gateway.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers