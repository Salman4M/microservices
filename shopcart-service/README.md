# Shopcart Service

A microservice for managing shopping carts in an e-commerce platform. Built with FastAPI and SQLAlchemy, this service provides cart management functionality with real-time stock verification, automatic cart creation, and event-driven integration with other services.

## Overview

The Shopcart Service is responsible for handling all shopping cart operations including cart creation, adding/removing items, updating quantities, and stock synchronization. It integrates with the product service for stock verification and automatically manages carts based on user lifecycle events from other microservices.

## Technologies

- **Framework**: FastAPI 0.118.0+
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0.43+
- **Migrations**: Alembic 1.17.0+
- **Message Broker**: RabbitMQ (Pika 1.3.2)
- **Task Queue**: Celery 5.5.3+ with Redis backend
- **HTTP Client**: httpx 0.28.1, requests 2.32.5
- **Python Version**: 3.11+

## Features

### Cart Management
- Automatic cart creation when users register
- One cart per user (shop owners cannot have carts)
- Cart retrieval by user UUID
- Cart deletion when user becomes shop owner

### Cart Items
- Add products to cart with product variation ID
- Update item quantities with stock verification
- Remove items from cart
- Automatic quantity increment for duplicate items
- Real-time stock availability checking

### Stock Verification
- Product existence verification via product service
- Stock availability checking before adding/updating items
- Automatic quantity adjustment if stock is insufficient
- Product active status validation

### Event-Driven Architecture
- Consumes `user.created` events to auto-create carts
- Consumes `order.created` events to clear cart after order
- Consumes `shop.approved` events to delete cart when user becomes seller
- Asynchronous event processing

### Background Tasks
- Periodic stock synchronization (every 5 minutes via Celery)
- Automatic removal of out-of-stock items
- Quantity adjustment based on available stock
- Cleanup of inactive or deleted products

## Architecture

### Components

1. **FastAPI Web Service**: Main application serving REST API endpoints
2. **RabbitMQ Consumer**: Background service consuming events from RabbitMQ
3. **Celery Worker**: Processes periodic tasks (stock sync)
4. **Celery Beat**: Scheduler for periodic tasks

### Database Models

- `ShopCart`: Shopping cart entity
  - Integer primary key
  - UUID foreign key to user
  - One-to-many relationship with CartItem
  - Timestamps (created_at, updated_at)
  
- `CartItem`: Individual items in cart
  - Integer primary key
  - Foreign key to ShopCart (CASCADE delete)
  - UUID reference to product variation
  - Quantity field
  - Timestamps

### API Structure

All endpoints are prefixed with `/shopcart/api/` and include:
- Cart creation and retrieval
- Item management (add, update, delete)

## Setup & Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 16
- RabbitMQ
- Redis (for Celery backend)
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and navigate to the service**:
```bash
cd shopcart-service
```

2. **Install dependencies** (using uv or pip):
```bash
uv sync
# or
pip install -r requirements.txt
```

3. **Configure environment variables**:
Create a `.env` file with:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/shopcart_db
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=your-password
DB_NAME=shopcart_db
DB_PORT=5432
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin12345
PRODUCT_SERVICE=http://localhost:8000
REDIS_URL=redis://localhost:6379/0
```

4. **Run database migrations**:
```bash
alembic upgrade head
```

5. **Start the FastAPI server**:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Start RabbitMQ consumer** (in separate terminal):
```bash
python consumer.py
```

7. **Start Celery worker** (in separate terminal):
```bash
celery -A src.shopcart_service.celery_app worker --loglevel=info
```

8. **Start Celery beat** (in separate terminal):
```bash
celery -A src.shopcart_service.celery_app beat --loglevel=info
```

### Docker Deployment

1. **Build and start services**:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- FastAPI web service
- RabbitMQ consumer service
- Celery worker
- Celery beat scheduler

2. **Access the service**:
- API: `http://localhost:8008` (if port mapping enabled)
- API Docs: `http://localhost:8008/docs`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `DB_HOST` | Database host | `localhost` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | Required |
| `DB_NAME` | Database name | `shopcart_db` |
| `DB_PORT` | Database port | `5432` |
| `RABBITMQ_HOST` | RabbitMQ host | `rabbitmq` |
| `RABBITMQ_PORT` | RabbitMQ port | `5672` |
| `RABBITMQ_USER` | RabbitMQ username | `admin` |
| `RABBITMQ_PASS` | RabbitMQ password | `admin12345` |
| `PRODUCT_SERVICE` | Product service URL | Required |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CLOUD_SQL_CONNECTION_NAME` | Cloud SQL connection (for Cloud Run) | Optional |
| `SKIP_MIGRATIONS` | Skip migrations on startup | `false` |
| `ENV` | Environment (development/production) | Optional |

### Celery Configuration

Celery is configured with:
- **Broker**: RabbitMQ (`amqp://admin:admin12345@rabbitmq:5672//`)
- **Backend**: Redis (`redis://redis_service:6379/0`)
- **Beat Schedule**: Stock sync every 5 minutes
- **Timezone**: UTC

## API Endpoints

### Cart Operations
- `POST /shopcart/api/` - Create a new cart
  - Requires: `X-User-Id` header
  - Returns: Created cart with items

- `GET /shopcart/api/mycart` - Get user's cart
  - Requires: `X-User-Id` header
  - Returns: Cart with all items

### Cart Items
- `POST /shopcart/api/items/{product_var_id}` - Add item to cart
  - Requires: `X-User-Id` header
  - Body: `CartItemCreate` (empty body, quantity defaults to 1)
  - Verifies product exists and stock availability
  - Returns: Created or updated cart item

- `PUT /shopcart/api/items/{item_id}` - Update cart item quantity
  - Requires: `X-User-Id` header
  - Body: `{quantity: int}`
  - Verifies stock availability for new quantity
  - Returns: Updated cart item

- `DELETE /shopcart/api/items/{item_id}` - Remove item from cart
  - Requires: `X-User-Id` header
  - Returns: Deleted cart item

## Authentication

The service uses header-based authentication. Include the `X-User-Id` header with a valid UUID in all requests:

```bash
curl -H "X-User-Id: <user-uuid>" http://localhost:8000/shopcart/api/mycart
```

## Event Messaging

### Consumed Events

The service consumes events from multiple exchanges:

#### User Events (`user_events` exchange)
- `user.created` - Automatically creates a shopping cart for new users
  - Payload: `{event_type, user_uuid, email, is_active}`

#### Order Events (`order_events` exchange)
- `order.created` - Clears cart items after successful order
  - Payload: `{event_type, data: {user_uuid, cart_id, order_id}}`

#### Shop Events (`shop_events` exchange)
- `shop.approved` - Deletes cart when user becomes shop owner
  - Payload: `{event_type, user_uuid, shop_id}`
  - Reason: Shop owners cannot have shopping carts

### Event Processing

- Events are processed asynchronously via RabbitMQ consumer
- Each event handler includes error handling and logging
- Failed events are nacked (not requeued) to prevent infinite loops
- Database transactions ensure data consistency

## Background Tasks

### Stock Synchronization

A Celery task runs every 5 minutes to synchronize cart items with product service:

- **Task**: `shopcart_service.tasks.sync_cart_stock`
- **Schedule**: Every 5 minutes (crontab: `*/5`)
- **Actions**:
  - Removes items for products that no longer exist
  - Removes items for inactive products
  - Removes items that are out of stock
  - Adjusts quantities if stock is lower than cart quantity
  - Logs all changes for monitoring

### Task Results

The sync task returns:
```json
{
  "status": "success",
  "total_items": 100,
  "updated": 5,
  "deleted": 10,
  "unchanged": 85,
  "errors": 0
}
```

## Product Service Integration

The service integrates with the Product Service to:

1. **Verify Product Existence**: Checks if product variation exists before adding to cart
2. **Check Stock Availability**: Validates stock before adding/updating items
3. **Verify Product Status**: Ensures product is active
4. **Get Stock Amount**: Retrieves current stock for quantity validation

### Product Client

The `ProductServiceDataCheck` class handles all product service interactions:
- `verify_product_exists(variation_id)`: Verifies product exists and is active
- `verify_stock(variation_id, quantity)`: Checks if sufficient stock is available

## Database Schema

### ShopCart Table
- `id`: Integer (Primary Key)
- `user_uuid`: UUID (Foreign Key to User)
- `created_at`: DateTime
- `updated_at`: DateTime

### CartItem Table
- `id`: Integer (Primary Key)
- `shop_cart_id`: Integer (Foreign Key to ShopCart, CASCADE delete)
- `product_variation_id`: UUID (Reference to Product Variation)
- `quantity`: Integer (default: 1)
- `created_at`: DateTime
- `updated_at`: DateTime

## Business Rules

1. **One Cart Per User**: Each user can have only one shopping cart
2. **Shop Owners Cannot Have Carts**: When a user becomes a shop owner, their cart is automatically deleted
3. **Stock Validation**: Items cannot be added/updated if stock is insufficient
4. **Automatic Quantity Increment**: Adding the same product again increments quantity instead of creating duplicate
5. **Cart Clearing**: Cart is cleared after order creation
6. **Stock Sync**: Periodic background task ensures cart items match available stock

## Testing

Run tests using pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=src/shopcart_service --cov-report=html
```

## API Documentation

Interactive API documentation is available via FastAPI's automatic docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Logging

The service uses Python's logging module with:
- Console output for development
- Structured logging for production
- Separate loggers for different components
- Error tracking and monitoring

## Error Handling

- **401 Unauthorized**: Missing or invalid `X-User-Id` header
- **404 Not Found**: Cart or cart item not found
- **400 Bad Request**: Invalid request data, insufficient stock, or product unavailable
- **503 Service Unavailable**: Product service connection issues

## License

This service is part of the EcommerceLocal platform.
