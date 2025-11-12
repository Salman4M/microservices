#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "Microservices Setup Script"
echo -e "======================================${NC}\n"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Create directory structure
echo -e "\n${YELLOW}Creating directory structure...${NC}"

directories=(
    "auth-service/src"
    "nginx/conf.d"
    "monitoring/grafana/provisioning/datasources"
    "monitoring/grafana/provisioning/dashboards"
    "monitoring/grafana/dashboards"
    "tests"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    echo -e "${GREEN}✓ Created $dir${NC}"
done

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cat > .env << 'EOF'
# JWT Configuration
JWT_SECRET=change-this-to-a-random-secret-key-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7

# User Service Database
USER_POSTGRES_DB=ecommerce_db
USER_POSTGRES_USER=ecommerce_user
USER_POSTGRES_PASSWORD=StrongPass123!

# Shop Service Database
SHOP_POSTGRES_DB=shop_service
SHOP_POSTGRES_USER=postgres
SHOP_POSTGRES_PASSWORD=postgres

# Order Service Database
ORDER_POSTGRES_DB=order_service
ORDER_POSTGRES_USER=postgres
ORDER_POSTGRES_PASSWORD=postgres

# ShopCart Service Database
SHOPCART_DB=shopcart_db
SHOPCART_USER=postgres
SHOPCART_PASSWORD=4444

# Wishlist Service Database
WISHLIST_DB=wishlist_db
WISHLIST_USER=postgres
WISHLIST_PASSWORD=postgres

# Django Secret
SECRET_KEY=django-insecure-change-this-in-production
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${BLUE}ℹ .env file already exists, skipping${NC}"
fi

# Stop existing containers
echo -e "\n${YELLOW}Stopping existing containers...${NC}"
docker-compose down -v 2>/dev/null || true

# Build and start services
echo -e "\n${YELLOW}Building and starting services...${NC}"
echo -e "${BLUE}This may take several minutes on first run...${NC}\n"

docker-compose up -d --build

# Wait for services to be ready
echo -e "\n${YELLOW}Waiting for services to initialize...${NC}"
sleep 30

# Check service health
echo -e "\n${YELLOW}Checking service health...${NC}"

check_service() {
    local name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name is ready${NC}"
            return 0
        fi
        echo -e "${BLUE}  Waiting for $name... (attempt $attempt/$max_attempts)${NC}"
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}✗ $name failed to start${NC}"
    return 1
}

# Check all services
check_service "Nginx Gateway" "http://localhost/"
check_service "Auth Service" "http://localhost/api/auth/health"
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3000/api/health"

# Print summary
echo -e "\n${BLUE}======================================"
echo "Setup Complete!"
echo -e "======================================${NC}\n"

echo -e "${GREEN}Services are now running:${NC}"
echo ""
echo "  🌐 API Gateway:      http://localhost"
echo "  🔐 Auth Service:     http://localhost/api/auth/"
echo "  📊 Prometheus:       http://localhost:9090"
echo "  📈 Grafana:          http://localhost:3000 (admin/admin)"
echo ""
echo -e "${GREEN}Swagger Documentation:${NC}"
echo "  📚 User Service:     http://localhost/user/docs"
echo "  📚 Shop Service:     http://localhost/shop/docs"
echo "  📚 Product Service:  http://localhost/product/docs"
echo "  📚 Order Service:    http://localhost/order/docs"
echo "  📚 Cart Service:     http://localhost/cart/docs"
echo "  📚 Wishlist Service: http://localhost/wishlist/docs"
echo ""
echo -e "${YELLOW}Run tests with:${NC}"
echo "  ./tests/test_microservices.sh"
echo "  python tests/test_api.py"
echo ""
echo -e "${YELLOW}View logs with:${NC}"
echo "  docker-compose logs -f"
echo ""
echo -e "${YELLOW}Stop services with:${NC}"
echo "  docker-compose down"
echo ""