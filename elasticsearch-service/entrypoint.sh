#!/usr/bin/env sh
set -e

echo "Starting Elasticsearch consumer..."

# Wait for Elasticsearch
python /app/consumer.py