#!/bin/bash

# Create shared network if not exists
docker network create shared_network 2>/dev/null || true

# Start Traefik first
echo "Starting Traefik..."
cd traefik-service
docker-compose up -d
cd ..

# Wait for Traefik to be ready
echo "Waiting for Traefik to start..."
sleep 5

# Start infrastructure services
echo "Starting Redis..."
cd redis-service
docker-compose up -d
cd ..

echo "Starting RabbitMQ..."
cd rabbitmq-service
docker-compose up -d
cd ..

# Start Gateway
echo "Starting Gateway Service..."
cd gateway-service
docker-compose up -d
cd ..

# Start backend services
echo "Starting User Service..."
cd user-service
docker-compose up -d
cd ..

echo "Starting Shop Service..."
cd shop-service
docker-compose up -d
cd ..

echo "Starting Product Service..."
cd product-service
docker-compose up -d
cd ..

echo "Starting Order Service..."
cd order-service
docker-compose up -d
cd ..

echo "Starting ShopCart Service..."
cd shopcart-service
docker-compose up -d
cd ..

echo "All services started!"
echo ""
echo "Access points:"
echo "- Traefik Dashboard: http://traefik.localhost:8080"
echo "- API Gateway: http://api.localhost"
echo "- Direct Gateway: http://localhost:8002"