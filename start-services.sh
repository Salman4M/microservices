#!/bin/bash

# Start all services

echo "Starting services..."
echo ""

# Ensure network exists
docker network create shared_network 2>/dev/null || echo "Network exists"
echo ""

# Start in order
cd redis-service 2>/dev/null && docker-compose up -d && cd .. || echo "Redis not found"
sleep 3

cd rabbitmq-service 2>/dev/null && docker-compose up -d && cd .. || echo "RabbitMQ not found"
sleep 5

cd traefik-service 2>/dev/null && docker-compose up -d && cd .. || echo "Traefik not found"
sleep 3

# cd elasticsearch-service 2>/dev/null && docker-compose up -d && cd .. || echo "Elasticsearch not found"
# sleep 10

cd user-service 2>/dev/null && docker-compose up -d && cd .. || echo "User not found"
sleep 3

cd shop-service 2>/dev/null && docker-compose up -d && cd .. || echo "Shop not found"
sleep 3

cd product-service 2>/dev/null && docker-compose up -d && cd .. || echo "Product not found"
sleep 5

# cd order-service 2>/dev/null && docker-compose up -d && cd .. || echo "Order not found"
# sleep 3

cd shopcart-service 2>/dev/null && docker-compose up -d && cd .. || echo "ShopCart not found"
sleep 3

cd wishlist-service 2>/dev/null && docker-compose up -d && cd .. || echo "Wishlist not found"
sleep 3

cd gateway-service 2>/dev/null && docker-compose up -d && cd .. || echo "Gateway not found"
sleep 5

echo ""
echo "All services started!"
echo ""
echo "URLs:"
echo "  Gateway: http://gateway.localhost/docs"
echo "  Elasticsearch: http://elasticsearch-api.localhost/docs"