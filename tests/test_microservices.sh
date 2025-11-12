#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost"
AUTH_TOKEN=""
USER_ID=""

echo "======================================"
echo "Microservices Integration Test Suite"
echo "======================================"
echo ""

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        echo "   Response: $3"
    fi
}

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local auth=$4
    
    if [ -n "$auth" ]; then
        curl -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $auth" \
            -d "$data"
    else
        curl -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

echo "Test 1: Nginx Gateway Health Check"
response=$(curl -s http://localhost/)
if echo "$response" | grep -q "status"; then
    print_result 0 "Nginx gateway is running"
else
    print_result 1 "Nginx gateway health check" "$response"
    exit 1
fi
echo ""

echo "Test 2: Prometheus Health Check"
response=$(curl -s http://localhost:9090/-/healthy)
if echo "$response" | grep -q "Prometheus"; then
    print_result 0 "Prometheus is running"
else
    print_result 1 "Prometheus health check" "$response"
fi
echo ""

echo "Test 3: Grafana Health Check"
response=$(curl -s http://localhost:3000/api/health)
if echo "$response" | grep -q "ok"; then
    print_result 0 "Grafana is running"
else
    print_result 1 "Grafana health check" "$response"
fi
echo ""

echo "Test 4: User Registration"
timestamp=$(date +%s)
test_email="test${timestamp}@example.com"
register_response=$(api_call POST "/user/api/user/register/" '{
    "first_name": "Test",
    "last_name": "User",
    "email": "'$test_email'",
    "password": "TestPass123!",
    "phone_number": "1234567890"
}')

if echo "$register_response" | grep -q "email"; then
    print_result 0 "User registration successful"
    USER_ID=$(echo "$register_response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
else
    print_result 1 "User registration" "$register_response"
fi
echo ""

echo "Test 5: User Login"
login_response=$(api_call POST "/api/auth/login" '{
    "email": "'$test_email'",
    "password": "TestPass123!"
}')

if echo "$login_response" | grep -q "access_token"; then
    AUTH_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    print_result 0 "User login successful"
else
    print_result 1 "User login" "$login_response"
    exit 1
fi
echo ""

echo "Test 6: Token Validation"
validation_response=$(api_call POST "/api/auth/validate" '{
    "token": "'$AUTH_TOKEN'"
}')

if echo "$validation_response" | grep -q '"valid":true'; then
    print_result 0 "Token validation successful"
else
    print_result 1 "Token validation" "$validation_response"
fi
echo ""

echo "Test 7: Get User Profile (Authenticated)"
profile_response=$(api_call GET "/user/api/user/profile/" "" "$AUTH_TOKEN")

if echo "$profile_response" | grep -q "$test_email"; then
    print_result 0 "Get user profile successful"
else
    print_result 1 "Get user profile" "$profile_response"
fi
echo ""

echo "Test 8: List Products (Public)"
products_response=$(api_call GET "/product/api/products/" "")

if echo "$products_response" | grep -q "\["; then
    print_result 0 "List products successful (public access)"
else
    print_result 1 "List products" "$products_response"
fi
echo ""

echo "Test 9: Access Protected Endpoint without Token"
cart_response=$(api_call GET "/cart/shopcart/api/mycart" "")

if echo "$cart_response" | grep -q "401"; then
    print_result 0 "Protected endpoint correctly requires authentication"
else
    print_result 1 "Protected endpoint access control" "$cart_response"
fi
echo ""

echo "Test 10: Create ShopCart (Authenticated)"
cart_create_response=$(api_call POST "/cart/shopcart/api/" "" "$AUTH_TOKEN")

if echo "$cart_create_response" | grep -q "id"; then
    print_result 0 "Create shopcart successful"
else
    print_result 1 "Create shopcart" "$cart_create_response"
fi
echo ""

echo "Test 11: Get User's Wishlist (Authenticated)"
wishlist_response=$(api_call GET "/wishlist/api/v1/wishlist" "" "$AUTH_TOKEN")

if echo "$wishlist_response" | grep -q "\["; then
    print_result 0 "Get wishlist successful"
else
    print_result 1 "Get wishlist" "$wishlist_response"
fi
echo ""

echo "Test 12: Logout"
logout_response=$(api_call POST "/api/auth/logout" "" "$AUTH_TOKEN")

if echo "$logout_response" | grep -q "message"; then
    print_result 0 "Logout successful"
else
    print_result 1 "Logout" "$logout_response"
fi
echo ""

echo "Test 13: Use Invalidated Token"
invalid_token_response=$(api_call GET "/user/api/user/profile/" "" "$AUTH_TOKEN")

if echo "$invalid_token_response" | grep -q "401"; then
    print_result 0 "Invalidated token correctly rejected"
else
    print_result 1 "Invalidated token check" "$invalid_token_response"
fi
echo ""

echo "Test 14: Check Swagger UI Endpoints"
swagger_endpoints=(
    "/user/docs"
    "/shop/docs"
    "/product/docs"
    "/order/docs"
    "/cart/docs"
    "/wishlist/docs"
)

for endpoint in "${swagger_endpoints[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    if [ "$response" = "200" ]; then
        print_result 0 "Swagger UI accessible at $endpoint"
    else
        print_result 1 "Swagger UI at $endpoint" "HTTP $response"
    fi
done
echo ""

echo "Test 15: Nginx Metrics Endpoint"
nginx_metrics=$(curl -s http://localhost/nginx_status)
if echo "$nginx_metrics" | grep -q "Active connections"; then
    print_result 0 "Nginx metrics endpoint working"
else
    print_result 1 "Nginx metrics" "$nginx_metrics"
fi
echo ""

echo "Test 16: Prometheus Targets"
targets=$(curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"up"' | wc -l)
if [ $targets -gt 0 ]; then
    print_result 0 "Prometheus has $targets healthy targets"
else
    print_result 1 "Prometheus targets" "No healthy targets found"
fi
echo ""

echo "======================================"
echo "Test Suite Complete"
echo "======================================"