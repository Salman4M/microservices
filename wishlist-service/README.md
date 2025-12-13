# Wishlist Service

A microservice for managing user wishlists in an e-commerce platform. Built with FastAPI and SQLModel, this service allows users to save products to their wishlist for later purchase and move them to their shopping cart.

## Overview

The Wishlist Service enables users to create and manage their wishlists, saving individual products (via product variations). It integrates with the product service to validate items before adding them to wishlists, with the shopping cart service to move items between wishlist and cart, and publishes events for analytics and other services. A Celery-based periodic task automatically removes inactive or deleted products from wishlists.

## Technologies

- **Framework**: FastAPI 0.124.0+
- **Database**: PostgreSQL 16
- **ORM**: SQLModel 0.0.27 (SQLAlchemy 2.0.44)
- **Migrations**: Alembic 1.17.2+
- **Message Broker**: RabbitMQ (aio-pika 9.5.8)
- **Task Queue**: Celery 5.6.0 with Redis backend
- **HTTP Client**: httpx 0.28.1
- **Python Version**: 3.13+

## Features

### Wishlist Management
- Add products to wishlist (by product variation ID)
- Remove items from wishlist
- Move items from wishlist to shopping cart
- View all wishlist items
- Get wishlist count
- Duplicate prevention (same product can't be added twice)

### Validation
- Product existence and active status verification via product service
- Stock availability check when moving to cart
- User ownership validation for all operations

### Automated Cleanup
- **Periodic Task**: Celery Beat runs every 3 minutes to check all wishlist items
- Automatically removes products that are:
  - Deleted from the product service
  - Marked as inactive (is_active=False)
  - No longer available

### Event-Driven Architecture
- Publishes `wishlist.created` events when items are added
- Publishes `wishlist.deleted` events when items are removed
- Consumes `user.created` events to create wishlists for new users
- Consumes `shop.approved` events to delete wishlists when users become shop owners

## Architecture

### Components

1. **FastAPI Web Service**: Main application serving REST API endpoints
2. **RabbitMQ Consumer**: Background service consuming user and shop events
3. **Celery Worker**: Executes periodic cleanup tasks
4. **Celery Beat**: Schedules periodic tasks (every 3 minutes)
5. **Event Publisher**: Publishes wishlist events to RabbitMQ

### Database Model

#### Wishlist Table
- `id`: Integer (Primary Key)
- `user_id`: String (Indexed, Unique - One wishlist per user)
- `created_at`: DateTime (Auto-generated)
- `updated_at`: DateTime (Nullable)

#### WishlistItem Table
- `id`: Integer (Primary Key)
- `wishlist_id`: Integer (Foreign Key to Wishlist)
- `product_variation_id`: String (Indexed)
- `created_at`: DateTime (Auto-generated)
- `updated_at`: DateTime (Nullable)
- **Unique Constraint**: `(wishlist_id, product_variation_id)`

### API Structure

All endpoints are prefixed with `/api/v1/` and include:
- Wishlist CRUD operations
- Move to cart functionality
- Wishlist count endpoint

## Setup & Installation

### Prerequisites

- Python 3.13+
- PostgreSQL 16
- RabbitMQ
- Redis (for Celery backend)
- Docker & Docker Compose

### Quick Start

1. **Create `.env` file**:
```env
DATABASE_URL=postgresql+psycopg://postgres:password@db:5432/wishlist_db
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
POSTGRES_DB=wishlist_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin12345

# Service URLs
PRODUCT_SERVICE_URL=http://fastapi_app:8000
SHOPCART_SERVICE_URL=http://shopcart_service:8000

# Celery
CELERY_BROKER_URL=amqp://admin:admin12345@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis_service:6379/0
```

2. **Start with Docker Compose**:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- FastAPI web service
- RabbitMQ consumer
- Celery worker
- Celery beat scheduler

3. **Access service**:
- API: `http://localhost:8003` (if port mapping enabled)
- API Docs: `http://localhost:8003/docs`
- Health Check: `http://localhost:8003/health`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | Application secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `POSTGRES_DB` | Database name | `wishlist_db` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | Required |
| `POSTGRES_HOST` | Database host | `db` |
| `POSTGRES_PORT` | Database port | `5432` |
| `RABBITMQ_HOST` | RabbitMQ host | `rabbitmq` |
| `RABBITMQ_PORT` | RabbitMQ port | `5672` |
| `RABBITMQ_USER` | RabbitMQ username | `admin` |
| `RABBITMQ_PASS` | RabbitMQ password | `admin12345` |
| `PRODUCT_SERVICE_URL` | Product service URL | Required |
| `SHOPCART_SERVICE_URL` | Shopping cart service URL | Required |
| `CELERY_BROKER_URL` | Celery broker URL | Required |
| `CELERY_RESULT_BACKEND` | Celery result backend | Required |

## API Endpoints

### Wishlist Operations

#### Add Item to Wishlist
```http
POST /api/v1/wishlist
Content-Type: application/json
X-User-Id: <user-uuid>

{
  "product_variation_id": "uuid-string"
}
```

**Validations:**
- Product must exist in product service
- Product must be active (is_active=True)
- Product cannot already be in user's wishlist

**Response:** `201 Created`
```json
{
  "id": 1,
  "product_variation_id": "uuid-string",
  "created_at": "2025-12-13T10:00:00Z",
  "updated_at": null
}
```

#### Get User's Wishlist
```http
GET /api/v1/wishlist
X-User-Id: <user-uuid>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": "user-uuid",
  "items": [
    {
      "id": 1,
      "product_variation_id": "product-uuid",
      "created_at": "2025-12-13T10:00:00Z",
      "updated_at": null
    }
  ],
  "created_at": "2025-12-13T09:00:00Z",
  "updated_at": null
}
```

#### Get Wishlist Count
```http
GET /api/v1/wishlist/count
X-User-Id: <user-uuid>
```

**Response:** `200 OK`
```json
{
  "user_id": "user-uuid",
  "wishlist_count": 5
}
```

#### Move Item to Cart
```http
POST /api/v1/wishlist/{item_id}/move-to-cart
X-User-Id: <user-uuid>
```

**Validations:**
- Item must exist in user's wishlist
- Product must still be active
- Product must have available stock
- User must have a shopping cart

**Response:** `200 OK`
```json
{
  "message": "Item successfully moved to cart",
  "cart_item": {
    "id": 42,
    "product_variation_id": "product-uuid",
    "quantity": 1,
    "created_at": "2025-12-13T10:30:00Z"
  },
  "removed_from_wishlist": 1
}
```

#### Remove Item from Wishlist
```http
DELETE /api/v1/wishlist/{item_id}
X-User-Id: <user-uuid>
```

**Response:** `200 OK`
```json
{
  "message": "Item removed from wishlist successfully"
}
```

## Authentication

The service uses header-based authentication. Include the `X-User-Id` header with a valid UUID in all requests:

```bash
curl -H "X-User-Id: <user-uuid>" http://localhost:8000/api/v1/wishlist
```

## Event Messaging

### Published Events

The service publishes events to the `wishlist_events` exchange:

#### wishlist.created
Published when an item is added to wishlist.

**Payload:**
```json
{
  "event_type": "wishlist.created",
  "wishlist_id": 1,
  "user_id": "user-uuid",
  "product_variation_id": "product-uuid",
  "shop_id": null,
  "timestamp": "2025-12-13T10:00:00Z",
  "metadata": {
    "source": "wishlist_service"
  }
}
```

#### wishlist.deleted
Published when an item is removed from wishlist.

**Payload:**
```json
{
  "event_type": "wishlist.deleted",
  "wishlist_id": 1,
  "user_id": "user-uuid",
  "timestamp": "2025-12-13T10:05:00Z",
  "metadata": {
    "source": "wishlist_service"
  }
}
```

### Consumed Events

The service consumes events from multiple exchanges:

#### user.created (from user_events exchange)
Automatically creates a wishlist for newly registered users (if they are active).

**Expected Payload:**
```json
{
  "event_type": "user.created",
  "user_uuid": "user-uuid",
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "timestamp": "2025-12-13T09:00:00Z"
}
```

#### shop.approved (from shop_events exchange)
Deletes the wishlist when a user becomes a shop owner (sellers don't need wishlists).

**Expected Payload:**
```json
{
  "event_type": "shop.approved",
  "user_uuid": "user-uuid",
  "shop_id": "shop-uuid",
  "is_shop_owner": true,
  "timestamp": "2025-12-13T11:00:00Z"
}
```

## Service Integration

### Product Service

**Endpoint:** `/api/products/variations/{variation_id}`

**Purpose:** 
- Validates product variation exists
- Checks if product is active (is_active=True)
- Called when adding items to wishlist
- Called periodically by Celery to verify product status

**Method:** GET request

**Response:**
```json
{
  "id": "variation-uuid",
  "product_id": "product-uuid",
  "amount": 10,
  "price": 29.99,
  "product": {
    "id": "product-uuid",
    "title": "Product Name",
    "is_active": true
  }
}
```

**Note:** Returns `None` if product doesn't exist or is inactive.

### ShopCart Service

**Endpoint:** `/api/items/{product_variation_id}`

**Purpose:** 
- Adds items to user's shopping cart
- Validates stock availability
- Called when moving items from wishlist to cart

**Method:** POST request with `X-User-Id` header

**Response:**
```json
{
  "id": 42,
  "shop_cart_id": 1,
  "product_variation_id": "product-uuid",
  "quantity": 1,
  "created_at": "2025-12-13T10:30:00Z"
}
```

## Periodic Tasks

### Inactive Products Cleanup

**Task Name:** `app.tasks.remove_inactive_products_from_wishlists`

**Schedule:** Every 3 minutes (180 seconds)

**Description:**
- Checks all products in all wishlists
- Verifies each product still exists and is active
- Removes items where:
  - Product not found (404 from product service)
  - Product exists but is_active=False
  - Product service returns None

**Logging:**
```
🔍 Starting inactive products cleanup task...
📊 Found 5 product items in wishlists to check
✓ Product abc-123 is active - keeping in wishlist
🗑️ Removing inactive product xyz-789 from wishlist item 15
✅ Cleanup completed - Checked: 5, Removed: 1, Kept: 4, Errors: 0
```

**Task Result:**
```json
{
  "status": "success",
  "total_items": 5,
  "checked": 5,
  "removed": 1,
  "kept": 4,
  "errors": 0
}
```

## Business Rules

1. **One Wishlist Per User**: Each user has exactly one wishlist
2. **No Duplicate Products**: Same product can't be added twice to the same wishlist
3. **Ownership Validation**: Users can only manage their own wishlist items
4. **Active Products Only**: Only active products can be added to wishlists
5. **Automatic Cleanup**: Inactive/deleted products are automatically removed every 3 minutes
6. **Shop Owners Exception**: When a user becomes a shop owner, their wishlist is deleted (shop owners sell, they don't buy)
7. **Stock Validation**: When moving to cart, product must have available stock

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful operation
- **201 Created**: Item successfully added to wishlist
- **400 Bad Request**: 
  - Missing required fields
  - Product already in wishlist
  - Insufficient stock (when moving to cart)
- **401 Unauthorized**: Missing or invalid `X-User-Id` header
- **403 Forbidden**: User trying to access another user's wishlist items
- **404 Not Found**: 
  - Wishlist not found
  - Wishlist item not found
  - Product not found
  - Shopping cart not found
- **503 Service Unavailable**: 
  - Product service unavailable
  - ShopCart service unavailable
  - Service connection timeout

### Example Error Responses

```json
{
  "detail": "Product variation not found in Product Service"
}
```

```json
{
  "detail": "Product already in wishlist"
}
```

```json
{
  "detail": "Product no longer available"
}
```

## Logging

The service uses Python's built-in logging with the following log levels:

### INFO Level
- Service startup/shutdown
- RabbitMQ connection status
- Database operations
- Event publishing/consuming
- Celery task execution
- Cleanup task results

### WARNING Level
- Product not found
- Product inactive
- Missing wishlist

### ERROR Level
- Service integration failures
- Database errors
- Event processing errors
- Celery task failures

### Example Logs

```
2025-12-13 10:00:00 - app.main - INFO - Starting Wishlist Service...
2025-12-13 10:00:01 - app.rabbitmq.connection - INFO - RabbitMQ connection established
2025-12-13 10:00:02 - app.tasks - INFO - 🔍 Starting inactive products cleanup task...
2025-12-13 10:00:03 - app.product_client - WARNING - Product variation xyz-789 exists but is inactive
2025-12-13 10:00:04 - app.tasks - INFO - 🗑️ Removing inactive product xyz-789 from wishlist item 15
2025-12-13 10:00:05 - app.tasks - INFO - ✅ Cleanup completed - Checked: 5, Removed: 1, Kept: 4, Errors: 0
```

## Docker Services

The `docker-compose.yml` defines 5 services:

1. **db**: PostgreSQL 16 database
2. **web**: FastAPI application (port 8000)
3. **consumer**: RabbitMQ event consumer
4. **celery_worker**: Celery worker for task execution
5. **celery_beat**: Celery beat scheduler for periodic tasks

### Service Dependencies

```
db (PostgreSQL)
  └─> web (FastAPI)
      ├─> consumer (RabbitMQ Consumer)
      ├─> celery_worker (Celery Worker)
      └─> celery_beat (Celery Beat)
```

### Networks

- **internal_net**: Internal communication between services
- **shared_network**: External network for cross-service communication

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload

# Start consumer (separate terminal)
python consumer.py

# Start Celery worker (separate terminal)
celery -A app.tasks worker --loglevel=info --queues=wishlist_queue

# Start Celery beat (separate terminal)
celery -A app.tasks beat --loglevel=info
```

### Creating Migrations

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Manual Task Execution

```bash
# Test cleanup task
celery -A app.tasks call app.tasks.test_wishlist_cleanup

# Force cleanup now
celery -A app.tasks call app.tasks.remove_inactive_products_from_wishlists
```

## API Documentation

Interactive API documentation is available via FastAPI's automatic docs:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Health Checks

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "wishlist",
  "rabbitmq": "connected"
}
```

## Monitoring

### Key Metrics to Monitor

1. **Celery Tasks**
   - Task execution time
   - Task success/failure rate
   - Removed items per cleanup run

2. **Database**
   - Wishlist item count
   - Query performance
   - Connection pool status

3. **RabbitMQ**
   - Message queue depth
   - Consumer lag
   - Failed message rate

4. **Service Integration**
   - Product service response time
   - ShopCart service response time
   - Service availability

## Troubleshooting

### Common Issues

**1. Products not being removed from wishlists**
- Check Celery beat is running: `docker logs wishlist_celery_beat`
- Check Celery worker logs: `docker logs wishlist_celery_worker`
- Verify Product Service is accessible

**2. Cannot add products to wishlist**
- Verify product exists in Product Service
- Check product is_active status
- Check for duplicate entries

**3. RabbitMQ connection issues**
- Verify RabbitMQ is running
- Check RABBITMQ_* environment variables
- Review consumer logs: `docker logs wishlist_consumer`

**4. Database connection errors**
- Check PostgreSQL is running
- Verify DATABASE_URL is correct
- Check database credentials

## License

This service is part of the EcommerceLocal platform.