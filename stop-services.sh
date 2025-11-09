#!/bin/bash

echo "🛑 Stopping all services..."

cd shopcart-service && docker-compose down && cd ..
cd order-service && docker-compose down && cd ..
cd product-service && docker-compose down && cd ..
cd shop-service && docker-compose down && cd ..
cd user-service && docker-compose down && cd ..
cd traefik-service && docker-compose down && cd ..
cd rabbitmq-service && docker-compose down && cd ..
cd redis-service && docker-compose down && cd ..

echo "✓ All services stopped"