# Wishlist Service

A microservice for managing user wishlists in an e-commerce platform. Built with FastAPI and SQLModel, this service allows users to save products and shops to their wishlist for later purchase.

## Overview

The Wishlist Service enables users to create and manage their wishlists, saving both individual products (via product variations) and entire shops. It integrates with the product and shop services to validate items before adding them to wishlists and publishes events for analytics and other services.

## Technologies

- **Framework**: FastAPI 0.115.0+
- **Database**: PostgreSQL 16
- **ORM**: SQLModel 0.0.22 (SQLAlchemy 2.0.44)
- **Migrations**: Alembic 1.17.0+
- **Message Broker**: RabbitMQ (aio-pika 9.4.3)
- **HTTP Client**: httpx 0.27.2
- **Python Version**: 3.11+

## Features

### Wishlist Management
- Add products to wishlist (by product variation ID)
- Add shops to wishlist (by shop ID)
- Remove items from wishlist
- View all wishlist items
- Get wishlist count
- Duplicate prevention (same item can't be added twice)

### Validation
- Product existence verification via product service
- Shop existence verification via shop service
- User ownership validation for deletion

### Event-Driven Architecture
- Publishes `wishlist.created` events when items are added
- Publishes `wishlist.deleted` events when items are removed
- Consumes `user.created` events (for future user wishlist initialization)

## Architecture

### Components

1. **FastAPI Web Service**: Main application serving REST API endpoints
2. **RabbitMQ Consumer**: Background service consuming user events
3. **Event Publisher**: Publishes wishlist events to RabbitMQ

### Database Model

- `Wishlist`: Main wishlist entity
  - Integer primary key
  - User ID (indexed)
  - Product variation ID (optional, indexed)
  - Shop ID (optional, indexed)
  - Created timestamp
  - Unique constraint on (user_id, product_variation_id, shop_id)

### API Structure

All endpoints are prefixed with `/api/v1/` and include:
- Wishlist CRUD operations
- Wishlist count endpoint

## Setup & Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 16
- RabbitMQ
- Docker & Docker Compose

### Quick Start

1. **Create `.env` file**:
```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/wishlist_db
SECRET_KEY=your-secret-key
DEBUG=True
POSTGRES_DB=wishlist_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin12345
PRODUCT_SERVICE_URL=http://product-service:8000
SHOP_SERVICE_URL=http://shop-service:8000
```

2. **Start with Docker**:
```bash
docker-compose up -d
```

This starts PostgreSQL, FastAPI service, and consumer automatically.

3. **Access service**:
- API: `http://localhost:8003` (if port mapping enabled)
- Docs: `http://localhost:8003/docs`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | Application secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `POSTGRES_DB` | Database name | Required |
| `POSTGRES_USER` | Database user | Required |
| `POSTGRES_PASSWORD` | Database password | Required |
| `RABBITMQ_HOST` | RabbitMQ host | `rabbitmq` |
| `RABBITMQ_PORT` | RabbitMQ port | `5672` |
| `RABBITMQ_USER` | RabbitMQ username | `admin` |
| `RABBITMQ_PASS` | RabbitMQ password | `admin12345` |
| `PRODUCT_SERVICE_URL` | Product service URL | Required |
| `SHOP_SERVICE_URL` | Shop service URL | Required |

## API Endpoints

### Wishlist Operations

- `POST /api/v1/wishlist` - Add item to wishlist
  - Requires: `X-User-Id` header
  - Body: `{product_variation_id?: string, shop_id?: string}`
  - Validates product/shop exists before adding
  - Returns: Created wishlist item

- `GET /api/v1/wishlist` - Get user's wishlist
  - Requires: `X-User-Id` header
  - Returns: List of wishlist items

- `GET /api/v1/wishlist/count` - Get wishlist count
  - Requires: `X-User-Id` header
  - Returns: `{user_id, wishlist_count}`

- `DELETE /api/v1/wishlist/{item_id}` - Remove item from wishlist
  - Requires: `X-User-Id` header
  - Validates user ownership
  - Returns: Success message

## Authentication

The service uses header-based authentication. Include the `X-User-Id` header with a valid UUID in all requests:

```bash
curl -H "X-User-Id: <user-uuid>" http://localhost:8000/api/v1/wishlist
```

## Event Messaging

### Published Events

The service publishes events to the `wishlist_events` exchange:

- `wishlist.created` - When an item is added to wishlist
  - Payload: `{wishlist_id, user_id, product_variation_id?, shop_id?}`

- `wishlist.deleted` - When an item is removed from wishlist
  - Payload: `{wishlist_id, user_id}`

### Consumed Events

The service consumes events from the `user_events` exchange:

- `user.created` - User registration event (for future wishlist initialization)

## Service Integration

### Product Service

- **Endpoint**: `/api/products/variations/{variation_id}`
- **Purpose**: Validates product variation exists before adding to wishlist
- **Method**: GET request with optional `X-User-ID` header

### Shop Service

- **Endpoint**: `/api/shops/{shop_id}/`
- **Purpose**: Validates shop exists before adding to wishlist
- **Method**: GET request with optional `X-User-ID` header
- **Cache**: Shop list endpoint (`/api/shops/`) is cached using Django's cache framework with a 10-minute TTL (600 seconds) for improved performance

## Business Rules

1. **One Item Per User**: Same product/shop can't be added twice for the same user
2. **Either Product or Shop**: Must provide either `product_variation_id` or `shop_id`, not both
3. **Ownership Validation**: Users can only delete their own wishlist items
4. **Existence Validation**: Product/shop must exist in respective services before adding

## Database Schema

### Wishlist Table

- `id`: Integer (Primary Key)
- `user_id`: String (Indexed, Foreign Key to User)
- `product_variation_id`: String (Optional, Indexed)
- `shop_id`: String (Optional, Indexed)
- `created_at`: DateTime (Auto-generated)

**Unique Constraint**: `(user_id, product_variation_id, shop_id)`

## Error Handling

- **401 Unauthorized**: Missing or invalid `X-User-Id` header
- **404 Not Found**: Wishlist item, product, or shop not found
- **400 Bad Request**: Invalid request data, duplicate item, or missing required fields
- **403 Forbidden**: User trying to delete another user's wishlist item
- **503 Service Unavailable**: Product or shop service connection issues

## Logging

Logs include:
- Request/response logging
- Event publishing status
- Service integration errors
- Database operations

## API Documentation

Interactive API documentation is available via FastAPI's automatic docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## License

This service is part of the EcommerceLocal platform.

