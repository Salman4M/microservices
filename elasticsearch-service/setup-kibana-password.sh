#!/bin/bash
set -e

ELASTIC_HOST="${ELASTIC_HOST:-http://elasticsearch:9200}"
ELASTIC_USER="${ELASTIC_USERNAME:-elastic}"
ELASTIC_PASS="${ELASTIC_PASSWORD}"
KIBANA_PASS="${KIBANA_SYSTEM_PASSWORD:-${ELASTIC_PASSWORD}}"

echo "Waiting for Elasticsearch to be ready..."
until curl -s -u "${ELASTIC_USER}:${ELASTIC_PASS}" "${ELASTIC_HOST}" > /dev/null 2>&1; do
  echo "Elasticsearch is unavailable - sleeping"
  sleep 2
done

echo "Elasticsearch is ready. Setting kibana_system password..."

# Set kibana_system password
curl -X POST -u "${ELASTIC_USER}:${ELASTIC_PASS}" \
  "${ELASTIC_HOST}/_security/user/kibana_system/_password" \
  -H "Content-Type: application/json" \
  -d "{\"password\":\"${KIBANA_PASS}\"}" \
  || echo "Password may already be set or failed to set"

echo "kibana_system password configured."
