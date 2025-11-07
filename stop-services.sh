#!/bin/bash

# Stop Traefik first
echo "Stoping Traefik..."
cd traefik-service
docker-compose down
cd ..

# Wait for Traefik to be ready
echo "Waiting for Traefik to stop..."
sleep 5

# Stop infrastructure services
echo "Stoping Redis..."
cd redis-service
docker-compose down
cd ..

echo "Stoping RabbitMQ..."
cd rabbitmq-service
docker-compose down
cd ..

# Start Gateway
echo "Stoping Gateway Service..."
cd gateway-service
docker-compose down
cd ..

# Start backend services
echo "Stoping User Service..."
cd user-service
docker-compose down
cd ..

echo "Stoping Shop Service..."
cd shop-service
docker-compose down
cd ..

echo "Stoping Product Service..."
cd product-service
docker-compose down
cd ..

echo "Stoping Order Service..."
cd order-service
docker-compose down
cd ..

echo "Stoping ShopCart Service..."
cd shopcart-service
docker-compose down
cd ..

echo "All services stopped!"
echo ""
# echo "Access points:"
# echo "- Traefik Dashboard: http://traefik.localhost:8080"
# echo "- API Gateway: http://api.localhost"
# echo "- Direct Gateway: http://localhost:8002"