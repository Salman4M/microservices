#!/bin/bash

echo "🚀 Starting all services..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create network
echo -e "${YELLOW}Creating shared network...${NC}"
docker network create shared_network 2>/dev/null || echo "Network already exists"

# Function to check container
check_container() {
    if [ "$(docker ps -q -f name=$1)" ]; then
        echo -e "${GREEN}✓ $1 is running${NC}"
    else
        echo "✗ $1 is not running"
    fi
}

# Start Redis
echo -e "${YELLOW}Starting Redis...${NC}"
cd redis-service && docker-compose up -d && cd ..
sleep 3

# Start RabbitMQ
echo -e "${YELLOW}Starting RabbitMQ...${NC}"
cd rabbitmq-service && docker-compose up -d && cd ..
sleep 5

# Start Traefik & Auth
echo -e "${YELLOW}Starting Traefik & Auth...${NC}"
cd traefik-service && docker compose -f docker-compose.dev.yml up -d && cd ..
sleep 5

# Start User Service
echo -e "${YELLOW}Starting User Service...${NC}"
cd user-service && docker-compose up -d && cd ..

# Start Shop Service
echo -e "${YELLOW}Starting Shop Service...${NC}"
cd shop-service && docker-compose up -d && cd ..

# Start Product Service
echo -e "${YELLOW}Starting Product Service...${NC}"
cd product-service && docker-compose up -d && cd ..

# Start Order Service
echo -e "${YELLOW}Starting Order Service...${NC}"
cd order-service && docker-compose up -d && cd ..

# Start ShopCart Service
echo -e "${YELLOW}Starting ShopCart Service...${NC}"
cd shopcart-service && docker-compose up -d && cd ..

echo ""
echo -e "${GREEN}=== Checking Status ===${NC}"
check_container "redis_service"
check_container "rabbitmq"
check_container "traefik_main"
check_container "auth_service"
check_container "web"  # user service
check_container "shop-service-web-1"
check_container "product-service-web-1"
check_container "order-service"
check_container "shopcart_service"

echo ""
echo -e "${GREEN}=== Service URLs ===${NC}"
echo "Traefik Dashboard: http://localhost:8080"
echo "Auth Service: http://localhost/auth/api"
echo "User Service: http://localhost/user/api"
echo "Shop Service: http://localhost/shop/api"
echo "Product Service: http://localhost/product/api"
echo "Order Service: http://localhost/order/api"
echo "ShopCart Service: http://localhost/shopcart/api"
echo "RabbitMQ: http://localhost/rabbitmq"
echo "Grafana: http://grafana.localhost"
echo "Prometheus: http://prometheus.localhost"

echo ""
echo -e "${GREEN}✓ All services started!${NC}"