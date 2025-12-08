# Analytics Service

A microservice for collecting and analyzing e-commerce data including orders, product views, shop views, and sales analytics. Built with Django REST Framework, this service provides comprehensive analytics capabilities for shops, products, and order performance tracking.

## Overview

The Analytics Service is responsible for collecting and processing analytics data from the e-commerce platform. It tracks order completions, product views, shop views, and provides detailed analytics dashboards for shops including revenue, sales reports, and product performance metrics. The service integrates with the product service to enrich order data with product information.

## Technologies

- **Framework**: Django 5.2+
- **API**: Django REST Framework 3.16.1
- **Database**: PostgreSQL 17
- **HTTP Client**: requests
- **API Documentation**: drf-spectacular 0.28.0, drf-yasg 1.21.11
- **Web Server**: Gunicorn 23+
- **Testing**: pytest, pytest-django
- **Python Version**: 3.10+

## Features

### Order Analytics
- Order completion tracking
- Order item enrichment with product data
- Revenue and profit calculations
- Order statistics and trends
- Idempotent order processing (prevents duplicates)

### Shop Analytics
- Shop dashboard with comprehensive statistics
- Sales reports with filtering and pagination
- Product performance metrics
- Daily revenue and order trends
- Top products by revenue
- Profit margin calculations

### Product View Analytics
- Track product views
- View statistics (total, 7 days, 30 days, 90 days)
- Product popularity metrics
- Percentage of total views
- All products view statistics

### Shop View Analytics
- Track shop views
- View statistics (total, 7 days, 30 days, 90 days)
- Shop popularity metrics
- Percentage of total views
- All shops view statistics

### Data Enrichment
- Automatic product data fetching from product service
- Order item enrichment with product details
- Shop and product information caching

## Architecture

### Components

1. **Web Service**: Main Django application serving REST API endpoints
2. **Analytics Service**: Business logic for processing orders and generating analytics
3. **Product Client**: HTTP client for fetching product data from product service

### Database Models

- `Shop`: Shop reference (external shop ID)
  - UUID primary key
  - External shop ID (unique)
  - Shop name
  - Created timestamp

- `Product`: Product reference (external product ID)
  - UUID primary key
  - External product ID (unique)
  - Product name
  - Created timestamp

- `ShopView`: Shop view tracking
  - UUID primary key
  - Foreign key to Shop
  - Viewed timestamp

- `ProductView`: Product view tracking
  - UUID primary key
  - Foreign key to Product
  - Viewed timestamp

- `Order`: Completed orders
  - UUID primary key
  - Order ID (unique, from order service)
  - User ID
  - Created timestamp
  - Enrichment status flag

- `OrderItem`: Order items with enriched data
  - UUID primary key
  - Foreign key to Order
  - Product variation ID
  - Quantity and price
  - Enriched fields: base_price, original_price, shop_id, product_id, product_title, product_sku, size, color
  - Indexed for performance (product_variation_id, shop_id, created_at)

### API Structure

All endpoints are prefixed with `/api/v1/` and include:
- Order completion processing
- Shop analytics endpoints
- Product view tracking
- Shop view tracking

### Service Integrations

- **Product Service**: Fetches product variation data to enrich order items
- **Order Service**: Receives order completion notifications

## Setup & Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 17
- Docker & Docker Compose (optional)
- Access to product service

### Local Development

1. **Clone and navigate to the service**:
```bash
cd analytic-service
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
Create a `.env` file with:
```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=analytic_db
DB_USER=analytic_user
DB_PASSWORD=12345
DB_HOST=localhost
DB_PORT=5432
PRODUCT_SERVICE_URL=http://localhost:8002
DOCKER=0
```

4. **Run migrations**:
```bash
python manage.py migrate
```

5. **Create superuser** (optional):
```bash
python manage.py createsuperuser
```

6. **Run the development server**:
```bash
python manage.py runserver
```

### Docker Deployment

1. **Build and start services**:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Django web service (Gunicorn)

2. **Access the service**:
- API: `http://localhost:8006` (if port mapping enabled)
- Admin: `http://analytic-admin.localhost` (via Traefik)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `True` |
| `DB_NAME` | Database name | `analytic_db` |
| `DB_USER` | Database user | `analytic_user` |
| `DB_PASSWORD` | Database password | `12345` |
| `DB_HOST` | Database host | `127.0.0.1` (local) / `db-analytic` (Docker) |
| `DB_PORT` | Database port | `5432` |
| `PRODUCT_SERVICE_URL` | Product service URL | `http://product-service:8000` |
| `DOCKER` | Docker environment flag | `0` |

## API Endpoints

### Order Analytics

- `POST /api/v1/analitic-order-completed/` - Process completed order
  - Body: `{id, user_id, created_at, items: [{id, product_variation, quantity, price}]}`
  - Returns: Order processing status
  - Idempotent: Returns 200 if order already exists

- `POST /api/v1/order-completed/` - Process completed order (ViewSet endpoint)
  - Same as above, alternative endpoint

### Shop Analytics

- `GET /api/v1/shops/{shop_id}/dashboard/` - Shop dashboard statistics
  - Query params: `days` (default: 30), `start_date`, `end_date`
  - Returns: Total revenue, orders, products sold, average order value, top products, daily trends

- `GET /api/v1/shops/{shop_id}/sales-report/` - Detailed sales report
  - Query params: `time_filter` (today, yesterday, last_7_days, last_30_days, last_90_days), `product_id`, `sort_by`, `order`, `page`, `page_size`
  - Returns: Paginated sales data with profit calculations

- `GET /api/v1/shops/{shop_id}/products-performance/` - Product performance metrics
  - Query params: `days` (default: 30), `limit` (default: 20)
  - Returns: Top products by revenue with profit margins

### Product View Analytics

- `POST /api/v1/product-view/` - Track product view
  - Body: `{product_uuid, product_name}`
  - Creates or updates product, records view

- `GET /api/v1/product-view/stats/` - Product view statistics
  - Query params: `product_id` (optional - if provided, single product stats; if not, all products)
  - Returns: View counts (total, 7 days, 30 days, 90 days), percentages

- `GET /api/v1/product-view/simple-stats/` - Simple product view stats
  - Query params: `days` (default: 30), `product_id` (optional)
  - Returns: Simplified view statistics

### Shop View Analytics

- `POST /api/v1/shop-view/` - Track shop view
  - Body: `{shop_uuid, shop_name}`
  - Creates or updates shop, records view

- `GET /api/v1/shop-view/stats/` - Shop view statistics
  - Query params: `shop_id` (optional - if provided, single shop stats; if not, all shops)
  - Returns: View counts (total, 7 days, 30 days, 90 days), percentages

- `GET /api/v1/shop-view/simple-stats/` - Simple shop view stats
  - Query params: `days` (default: 30), `shop_id` (optional)
  - Returns: Simplified view statistics

## Order Processing Flow

1. **Order Service** sends completed order to `/api/v1/analitic-order-completed/`
2. **Analytics Service** receives order data:
   - Creates or updates Order record (idempotent)
   - For each order item:
     - Fetches product variation data from product service
     - Enriches order item with product details (title, SKU, shop_id, etc.)
     - Creates or updates OrderItem record
3. **Response**: Returns success status with order details

### Idempotency

Order processing is idempotent:
- If order with same `order_id` already exists, returns 200 OK
- Prevents duplicate order processing
- Handles retries gracefully

## Analytics Calculations

### Shop Dashboard

- **Total Revenue**: Sum of (price × quantity) for all order items
- **Total Orders**: Distinct order count
- **Total Products Sold**: Sum of quantities
- **Average Order Value**: Total revenue / Total orders
- **Conversion Rate**: (Total orders / Total products sold) × 100
- **Top Products**: Products sorted by revenue (top 10)
- **Daily Trends**: Daily revenue and order counts

### Sales Report

- **Total Revenue**: Sum of (price × quantity)
- **Total Profit**: Sum of ((price - base_price) × quantity)
- **Average Order Value**: Total revenue / Total orders
- **Profit per Item**: price - base_price
- **Total Profit**: profit_per_item × quantity

### Product Performance

- **Total Sold**: Sum of quantities
- **Total Revenue**: Sum of (price × quantity)
- **Total Profit**: Sum of ((price - base_price) × quantity)
- **Average Price**: Average of prices
- **Order Count**: Distinct order count
- **Profit Margin**: (Total profit / Total revenue) × 100

## Testing

Run tests using pytest:

```bash
pytest
```

Or with Django test runner:

```bash
python manage.py test
```

Test files are located in `analitic/tests/`:
- `test_models.py` - Model tests
- `test_serializers.py` - Serializer tests
- `test_views.py` - View tests
- `test_integration.py` - Integration tests

## API Documentation

Interactive API documentation is available via Swagger/OpenAPI at:
- `/api/schema/swagger-ui/` - Swagger UI
- `/api/schema/redoc/` - ReDoc
- `/api/schema/` - OpenAPI schema

## Service Clients

### Product Client

- `get_product_variation_data(variation_id)` - Fetch product variation data
  - Returns: `{base_price, original_price, size, color, product_title, product_sku, shop_id}`
  - Used for enriching order items

## Data Models

### Order Item Enrichment

When processing orders, the service enriches order items with:
- `base_price`: Product base price from product service
- `original_price`: Original price before discount
- `size`: Product variation size
- `color`: Product variation color
- `product_title`: Product title
- `product_sku`: Product SKU
- `shop_id`: Shop ID from product
- `product_id`: Product ID from product service

## Logging

Logs are written to:
- Console: Standard output
- Django logging system

Log levels are configurable via Django settings.

## Static & Media Files

- Static files: Collected to `staticfiles/` directory
- Served via WhiteNoise middleware

## Error Handling

### Order Processing Errors

- **400 Bad Request**: Missing required fields
- **200 OK**: Order already exists (idempotent response)
- **500 Internal Server Error**: Processing errors

### Analytics Query Errors

- **404 Not Found**: Shop or product not found
- **500 Internal Server Error**: Query processing errors

## Security Features

- CSRF protection
- SQL injection protection (Django ORM)
- Input validation via serializers
- UUID validation

## Performance Considerations

- Database indexes on:
  - `OrderItem.product_variation_id`
  - `OrderItem.shop_id`
  - `OrderItem.created_at`
- Efficient aggregation queries
- Pagination for large datasets
- Query optimization for analytics calculations

## License

This service is part of the EcommerceLocal platform.

