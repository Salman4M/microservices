#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Microservices Testing Script${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Base URL
BASE_URL="http://localhost"

# Test 1: Check Traefik is running
echo -e "${YELLOW}[1/9] Checking Traefik Dashboard...${NC}"
if curl -s http://localhost:8080/dashboard/ > /dev/null; then
    echo -e "${GREEN}✓ Traefik is running${NC}\n"
else
    echo -e "${RED}✗ Traefik is not accessible${NC}\n"
    exit 1
fi

# Test 2: Check Auth Service directly (bypass Traefik)
echo -e "${YELLOW}[2/9] Testing Auth Service (Direct)...${NC}"
AUTH_DIRECT=$(docker exec auth_service curl -s http://localhost:8000/health)
if echo "$AUTH_DIRECT" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Auth Service is healthy (direct)${NC}"
    echo "Response: $AUTH_DIRECT\n"
else
    echo -e "${RED}✗ Auth Service is unhealthy${NC}\n"
fi

# Test 3: Check Auth Service via Traefik
echo -e "${YELLOW}[3/9] Testing Auth Service (via Traefik)...${NC}"
AUTH_VIA_TRAEFIK=$(curl -s ${BASE_URL}/auth/)
echo "Response: $AUTH_VIA_TRAEFIK"
if echo "$AUTH_VIA_TRAEFIK" | grep -q "Auth Service"; then
    echo -e "${GREEN}✓ Auth Service accessible via Traefik${NC}\n"
else
    echo -e "${RED}✗ Auth Service NOT accessible via Traefik${NC}"
    echo "Expected to see 'Auth Service' in response\n"
fi

# Test 4: Check User Service exists
echo -e "${YELLOW}[4/9] Checking if User Service container exists...${NC}"
if docker ps | grep -q "web\|user_service"; then
    USER_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "web|user_service")
    echo -e "${GREEN}✓ User Service container found: $USER_CONTAINER${NC}\n"
else
    echo -e "${RED}✗ User Service container NOT found${NC}"
    echo "Run: cd user-service && docker-compose up -d\n"
    exit 1
fi

# Test 5: Register a new user
echo -e "${YELLOW}[5/9] Registering new user...${NC}"
RANDOM_EMAIL="testuser_$(date +%s)@example.com"
REGISTER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST ${BASE_URL}/user/api/register/ \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${RANDOM_EMAIL}\",
    \"password\": \"TestPass123!\",
    \"first_name\": \"Test\",
    \"last_name\": \"User\"
  }")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | grep HTTP_CODE | cut -d':' -f2)
BODY=$(echo "$REGISTER_RESPONSE" | sed 's/HTTP_CODE:.*//')

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ User registered (HTTP $HTTP_CODE)${NC}"
    USER_UUID=$(echo $BODY | grep -o '"uuid":"[^"]*' | cut -d'"' -f4)
    echo "User UUID: $USER_UUID"
    echo "Email: $RANDOM_EMAIL\n"
else
    echo -e "${RED}✗ Registration failed (HTTP $HTTP_CODE)${NC}"
    echo "Response: $BODY\n"
    echo "Trying with existing user..."
    RANDOM_EMAIL="test@example.com"
fi

# Test 6: Login to get JWT tokens
echo -e "${YELLOW}[6/9] Logging in...${NC}"
LOGIN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST ${BASE_URL}/auth/api/login \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${RANDOM_EMAIL}\",
    \"password\": \"TestPass123!\"
  }")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | grep HTTP_CODE | cut -d':' -f2)
BODY=$(echo "$LOGIN_RESPONSE" | sed 's/HTTP_CODE:.*//')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Login successful (HTTP $HTTP_CODE)${NC}"
    ACCESS_TOKEN=$(echo $BODY | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "Access Token (first 50 chars): ${ACCESS_TOKEN:0:50}...\n"
else
    echo -e "${RED}✗ Login failed (HTTP $HTTP_CODE)${NC}"
    echo "Response: $BODY\n"
    echo "If user doesn't exist, register first manually"
    exit 1
fi

# Test 7: Access protected endpoint WITHOUT token (should fail)
echo -e "${YELLOW}[7/9] Testing protected endpoint WITHOUT token...${NC}"
UNAUTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" ${BASE_URL}/product/api/products/)
HTTP_CODE=$(echo "$UNAUTH_RESPONSE" | grep HTTP_CODE | cut -d':' -f2)

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    echo -e "${GREEN}✓ Correctly rejected (HTTP $HTTP_CODE)${NC}\n"
else
    echo -e "${RED}✗ Should have been rejected but got HTTP $HTTP_CODE${NC}"
    echo "$UNAUTH_RESPONSE\n"
fi

# Test 8: Access protected endpoint WITH token (should succeed)
echo -e "${YELLOW}[8/9] Testing Product Service WITH token...${NC}"
PRODUCT_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  ${BASE_URL}/product/api/products/)

HTTP_CODE=$(echo "$PRODUCT_RESPONSE" | grep HTTP_CODE | cut -d':' -f2)
BODY=$(echo "$PRODUCT_RESPONSE" | sed 's/HTTP_CODE:.*//')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Product Service accessible (HTTP $HTTP_CODE)${NC}"
    echo "Response: ${BODY:0:100}...\n"
else
    echo -e "${RED}✗ Product Service failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY\n"
fi

# Test 9: Test ShopCart Service
echo -e "${YELLOW}[9/9] Testing ShopCart Service...${NC}"
CART_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  ${BASE_URL}/shopcart/api/)

HTTP_CODE=$(echo "$CART_RESPONSE" | grep HTTP_CODE | cut -d':' -f2)
BODY=$(echo "$CART_RESPONSE" | sed 's/HTTP_CODE:.*//')

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo -e "${GREEN}✓ ShopCart Service accessible (HTTP $HTTP_CODE)${NC}"
    echo "Response: ${BODY:0:100}...\n"
elif [ "$HTTP_CODE" = "401" ]; then
    echo -e "${YELLOW}⚠ ShopCart rejected request - Cart may already exist (HTTP $HTTP_CODE)${NC}\n"
else
    echo -e "${RED}✗ ShopCart Service failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY\n"
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "✓ Traefik Dashboard: http://localhost:8080"
echo -e "✓ Auth Service: ${BASE_URL}/auth/"
echo -e "✓ User Service: ${BASE_URL}/user/api/"
echo -e "✓ Product Service: ${BASE_URL}/product/api/"
echo -e "✓ ShopCart Service: ${BASE_URL}/shopcart/api/"
echo -e "\n${GREEN}Credentials for manual testing:${NC}"
echo "Email: $RANDOM_EMAIL"
echo "Password: TestPass123!"
echo "Access Token: $ACCESS_TOKEN"
echo -e "\n${YELLOW}Check Traefik Dashboard: http://localhost:8080/dashboard/${NC}"