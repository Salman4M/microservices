#!/bin/bash

# Simple Stop Script - Stops all services safely

echo "Stopping services..."
echo ""

# Stop in reverse order
cd traefik-service 2>/dev/null && docker-compose down && cd .. || echo "Traefik not found"
cd gateway-service 2>/dev/null && docker-compose down && cd .. || echo "Gateway not found"
cd elasticsearch-service 2>/dev/null && docker-compose down && cd .. || echo "Elasticsearch not found"
cd product-service 2>/dev/null && docker-compose down && cd .. || echo "Product not found"
cd shop-service 2>/dev/null && docker-compose down && cd .. || echo "Shop not found"
cd user-service 2>/dev/null && docker-compose down && cd .. || echo "User not found"
cd order-service 2>/dev/null && docker-compose down && cd .. || echo "Order not found"
cd shopcart-service 2>/dev/null && docker-compose down && cd .. || echo "ShopCart not found"
cd wishlist-service 2>/dev/null && docker-compose down && cd .. || echo "Wishlist not found"
cd rabbitmq-service 2>/dev/null && docker-compose down && cd .. || echo "RabbitMQ not found"
cd redis-service 2>/dev/null && docker-compose down && cd .. || echo "Redis not found"

echo ""
echo "All services stopped!"