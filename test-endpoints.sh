#!/bin/bash
# Complete Endpoint Testing Guide
# Make executable: chmod +x test-endpoints.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Complete Endpoint Testing${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test 1: Traefik Dashboard
echo -e "${YELLOW}[1] Traefik Dashboard${NC}"
DASHBOARD=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/dashboard/)
if [ "$DASHBOARD" = "200" ]; then
    echo -e "${GREEN}✓ http://localhost:8080/dashboard/ (HTTP $DASHBOARD)${NC}"
else
    echo -e "${RED}✗ Dashboard failed (HTTP $DASHBOARD)${NC}"
fi
echo ""

# Test 2: Auth Service Endpoints
echo -e "${YELLOW}[2] Auth Service${NC}"
echo -e "${BLUE}Testing root endpoint:${NC}"
AUTH_ROOT=$(curl -s ${BASE_URL}/auth/ | jq -r '.service' 2>/dev/null)
if [ "$AUTH_ROOT" = "Auth Service" ]; then
    echo -e "${GREEN}✓ ${BASE_URL}/auth/ - Working${NC}"
else
    echo -e "${RED}✗ ${BASE_URL}/auth/ - Failed${NC}"
fi

echo -e "${BLUE}Testing docs endpoint:${NC}"
AUTH_DOCS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/auth/docs)
if [ "$AUTH_DOCS" = "200" ]; then
    echo -e "${GREEN}✓ ${BASE_URL}/auth/docs (HTTP $AUTH_DOCS)${NC}"
else
    echo -e "${RED}✗ ${BASE_URL}/auth/docs (HTTP $AUTH_DOCS)${NC}"
fi

echo -e "${BLUE}Testing OpenAPI endpoint:${NC}"
AUTH_OPENAPI=$(curl -s ${BASE_URL}/auth/openapi.json | jq -r '.openapi' 2>/dev/null)
if [ -n "$AUTH_OPENAPI" ]; then
    echo -e "${GREEN}✓ ${BASE_URL}/auth/openapi.json - Working (OpenAPI $AUTH_OPENAPI)${NC}"
else
    echo -e "${RED}✗ ${BASE_URL}/auth/openapi.json - Failed${NC}"
fi
echo ""

# Test 3: User Service
echo -e "${YELLOW}[3] User Service${NC}"
echo -e "${BLUE}Testing health endpoint:${NC}"
USER_HEALTH=$(curl -s ${BASE_URL}/user/api/health/ | jq -r '.status' 2>/dev/null)
if [ "$USER_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ ${BASE_URL}/user/api/health/ - Healthy${NC}"
else
    echo -e "${RED}✗ ${BASE_URL}/user/api/health/ - Unhealthy${NC}"
fi

echo -e "${BLUE}Testing docs endpoint:${NC}"
USER_DOCS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/user/api/schema/swagger/)
if [ "$USER_DOCS" = "200" ]; then
    echo -e "${GREEN}✓ ${BASE_URL}/user/api/schema/swagger/ (HTTP $USER_DOCS)${NC}"
else
    echo -e "${RED}✗ ${BASE_URL}/user/api/schema/swagger/ (HTTP $USER_DOCS)${NC}"
fi
echo ""

# Test 4: Shop Service
echo -e "${YELLOW}[4] Shop Service${NC}"
echo -e "${BLUE}Testing admin panel:${NC}"
SHOP_ADMIN=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/shop-admin/)
if [ "$SHOP_ADMIN" = "200" ] || [ "$SHOP_ADMIN" = "302" ]; then
    echo -e "${GREEN}✓ ${BASE_URL}/shop-admin/ (HTTP $SHOP_ADMIN)${NC}"
else
    echo -e "${RED}✗ ${BASE_URL}/shop-admin/ (HTTP $SHOP_ADMIN)${NC}"
fi

echo -e "${BLUE}Testing docs endpoint:${NC}"
SHOP_DOCS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/shop/schema/swagger/)
if [ "$SHOP_DOCS" = "200" ]; then
    echo -e "${GREEN}✓ ${BASE_URL}/shop/schema/swagger/ (HTTP $SHOP_DOCS)${NC}"
else
    echo -e "${RED}✗ ${BASE_URL}/shop/schema/swagger/ (HTTP $SHOP_DOCS)${NC}"
fi

echo -e "${BLUE}Testing protected API (should require auth):${NC}"
SHOP_LIST=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/shop/api/shops/)
if [ "$SHOP_LIST" = "401" ]; then
    echo -e "${GREEN}✓ ${BASE_URL}/shop/api/shops/ - Protected (HTTP $SHOP_LIST)${NC}"
elif [ "$SHOP_LIST" = "200" ]; then
    echo -e "${YELLOW}⚠ ${BASE_URL}/shop/api/shops/ - Not protected (HTTP $SHOP_LIST)${NC}"
else
    echo -e "${RED}✗ ${BASE_URL}/shop/api/shops/ (HTTP $SHOP_LIST)${NC}"
fi
echo ""

# Test 5: Authentication Flow
echo -e "${YELLOW}[5] Complete Authentication Flow${NC}"
echo -e "${BLUE}Step 1: Register user${NC}"
RANDOM_EMAIL="testuser_$(date +%s)@example.com"
REGISTER_RESPONSE=$(curl -s -X POST ${BASE_URL}/user/api/register/ \
  -H 'Content-Type: application/json' \
  -d "{
    \"email\": \"${RANDOM_EMAIL}\",
    \"password\": \"TestPass123!\",
    \"first_name\": \"Test\",
    \"last_name\": \"User\"
  }")

USER_UUID=$(echo $REGISTER_RESPONSE | jq -r '.uuid' 2>/dev/null)
if [ -n "$USER_UUID" ] && [ "$USER_UUID" != "null" ]; then
    echo -e "${GREEN}✓ User registered: $RANDOM_EMAIL (UUID: $USER_UUID)${NC}"
else
    echo -e "${YELLOW}⚠ Registration issue (user may already exist)${NC}"
    RANDOM_EMAIL="test@example.com"
fi

echo -e "${BLUE}Step 2: Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST ${BASE_URL}/auth/api/login \
  -H 'Content-Type: application/json' \
  -d "{
    \"email\": \"${RANDOM_EMAIL}\",
    \"password\": \"TestPass123!\"
  }")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token' 2>/dev/null)
if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    echo -e "  Token: ${ACCESS_TOKEN:0:30}..."
else
    echo -e "${RED}✗ Login failed${NC}"
    echo -e "$LOGIN_RESPONSE"
    exit 1
fi

echo -e "${BLUE}Step 3: Access protected user profile${NC}"
PROFILE_RESPONSE=$(curl -s ${BASE_URL}/user/api/profile/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

PROFILE_EMAIL=$(echo $PROFILE_RESPONSE | jq -r '.email' 2>/dev/null)
if [ "$PROFILE_EMAIL" = "$RANDOM_EMAIL" ]; then
    echo -e "${GREEN}✓ Profile access successful${NC}"
else
    echo -e "${RED}✗ Profile access failed${NC}"
fi

echo -e "${BLUE}Step 4: Create shop${NC}"
SHOP_RESPONSE=$(curl -s -X POST ${BASE_URL}/shop/api/create/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test Shop '"$(date +%s)"'",
    "about": "Automated test shop"
  }')

SHOP_NAME=$(echo $SHOP_RESPONSE | jq -r '.name' 2>/dev/null)
if [ -n "$SHOP_NAME" ] && [ "$SHOP_NAME" != "null" ]; then
    echo -e "${GREEN}✓ Shop created: $SHOP_NAME${NC}"
elif echo "$SHOP_RESPONSE" | grep -q "already have Shop"; then
    echo -e "${YELLOW}⚠ User already has a shop${NC}"
else
    echo -e "${RED}✗ Shop creation failed${NC}"
    echo -e "$SHOP_RESPONSE"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Test credentials:"
echo -e "  Email: $RANDOM_EMAIL"
echo -e "  Password: TestPass123!"
echo -e "  Token: $ACCESS_TOKEN"
echo -e "\n${GREEN}All critical endpoints tested!${NC}"
echo -e "\nAccess points:"
echo -e "  • Traefik Dashboard: ${BLUE}http://localhost:8080${NC}"
echo -e "  • Auth Docs: ${BLUE}http://localhost/auth/docs${NC}"
echo -e "  • User Docs: ${BLUE}http://localhost/user/api/schema/swagger/${NC}"
echo -e "  • Shop Admin: ${BLUE}http://localhost/shop-admin/${NC}"
echo -e "  • Shop Docs: ${BLUE}http://localhost/shop/schema/swagger/${NC}"