# Ecommerce - Microservices E-Commerce Platform

A comprehensive, production-ready e-commerce platform built with microservices architecture. This platform provides a complete solution for online shopping with shop management, product catalog, order processing, analytics, and search capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Services](#services)
- [Technologies](#technologies)
- [Getting Started](#getting-started)
- [Service Communication](#service-communication)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Future Features](#future-features)

## 🎯 Overview

EcommerceLocal is a distributed e-commerce platform that follows microservices architecture principles. The platform is designed to be scalable, maintainable, and resilient, with each service handling a specific business domain.

### Key Features

- **User Management**: Registration, authentication, profile management
- **Shop Management**: Multi-vendor support with shop approval workflow
- **Product Catalog**: Products, variations, categories, images, comments
- **Shopping Cart**: Real-time stock validation and cart management
- **Order Processing**: Complete order lifecycle with status tracking
- **Wishlist**: Save products and shops for later
- **Analytics**: Comprehensive sales and performance analytics
- **Search**: Full-text search across shops and products using Elasticsearch
- **API Gateway**: Unified entry point with authentication and routing

## 🏗️ Architecture

### Architecture Overview

```
┌─────────────┐
│   Clients   │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│         Traefik (Reverse Proxy)            │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│      Gateway Service (API Gateway)         │
│  - JWT Authentication                        │
│  - Request Routing                          │
│  - Unified API Documentation                │
└──────┬──────────────────────────────────────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       │              │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│   User      │ │   Shop     │ │  Product   │ │   Order    │
│  Service    │ │  Service   │ │  Service   │ │  Service   │
└─────────────┘ └────────────┘ └────────────┘ └────────────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                                     │                       
                        ┌────────────┼────────────┐
                        │            │            │
                    ┌────▼────┐  ┌────▼────┐  ┌───▼────┐
                    │ Shopcart│  │Wishlist │  │Analytic│
                    │ Service │  │ Service │  │Service │
                    └─────────┘  └─────────┘  └────────┘
```

### Communication Patterns

1. **Synchronous**: HTTP/REST API calls between services
2. **Asynchronous**: RabbitMQ message broker for event-driven communication
3. **Caching**: Redis for token blacklisting and session management
4. **Search**: Elasticsearch for full-text search capabilities

## 🔧 Services

### Core Business Services

#### 1. User Service
- **Framework**: Django REST Framework
- **Database**: PostgreSQL 16
- **Features**:
  - User registration and authentication
  - Profile management with image upload
  - Password reset functionality
  - Shop owner status tracking
- **Documentation**: [user-service/README.md](user-service/README.md)

#### 2. Shop Service
- **Framework**: Django REST Framework
- **Database**: PostgreSQL 16
- **Features**:
  - Shop creation and management
  - Shop approval workflow (PENDING, APPROVED, REJECTED)
  - Branch management with geolocation
  - Comments and ratings
  - Media uploads
  - Social media integration
  - Order item tracking
- **Documentation**: [shop-service/README.md](shop-service/README.md)

#### 3. Product Service
- **Framework**: FastAPI
- **Database**: PostgreSQL 15+
- **Features**:
  - Product CRUD operations
  - Category management
  - Product variations (size, color, etc.)
  - Stock management
  - Product images
  - Comments on products
  - Automatic stock reduction on order
- **Documentation**: [product-service/README.md](product-service/README.md)

#### 4. Order Service
- **Framework**: Django REST Framework
- **Database**: PostgreSQL 16
- **Features**:
  - Order creation from shopping cart
  - Order item management
  - Status tracking (Processing, Shipped, Delivered, Cancelled)
  - Stock validation before order creation
  - Automatic order approval
  - Integration with analytics
- **Documentation**: [order-service/README.md](order-service/README.md)

#### 5. Shopcart Service
- **Framework**: FastAPI
- **Database**: PostgreSQL 16
- **Features**:
  - Shopping cart management
  - Real-time stock verification
  - Automatic cart creation on user registration
  - Cart clearing after order
  - Periodic stock synchronization (Celery)
- **Documentation**: [shopcart-service/README.md](shopcart-service/README.md)

#### 6. Wishlist Service
- **Framework**: FastAPI
- **Database**: PostgreSQL 16
- **Features**:
  - Add products to wishlist
  - Add shops to wishlist
  - Wishlist management
  - Product/shop validation
- **Documentation**: [wishlist-service/README.md](wishlist-service/README.md)

#### 7. Analytics Service
- **Framework**: Django REST Framework
- **Database**: PostgreSQL 17
- **Features**:
  - Order analytics and revenue tracking
  - Shop dashboard with statistics
  - Product view analytics
  - Shop view analytics
  - Sales reports with filtering
  - Product performance metrics
- **Documentation**: [analytic-service/README.md](analytic-service/README.md)

#### 8. Elasticsearch Service
- **Framework**: FastAPI
- **Search Engine**: Elasticsearch 8.12.1
- **Features**:
  - Full-text search across shops and products
  - Fuzzy matching for typo tolerance
  - Real-time index updates via events
  - Shop-specific product search
  - Kibana integration for visualization
- **Documentation**: [elasticsearch-service/README.md](elasticsearch-service/README.md)

### Infrastructure Services

#### 9. Gateway Service
- **Framework**: FastAPI
- **Features**:
  - Single entry point for all API requests
  - JWT token validation and management
  - Request routing to backend services
  - Unified OpenAPI documentation
  - Token blacklisting via Redis
- **Documentation**: [gateway-service/README.md](gateway-service/README.md)

#### 10. Traefik Service
- **Technology**: Traefik v2.10
- **Features**:
  - Reverse proxy and load balancing
  - Service discovery via Docker labels
  - SSL/TLS termination
  - Automatic routing
- **Documentation**: [traefik-service/README.md](traefik-service/README.md)

#### 11. RabbitMQ Service
- **Technology**: RabbitMQ 3-management
- **Features**:
  - Message broker for event-driven architecture
  - Topic exchanges for event routing
  - Web-based management interface
  - Reliable message delivery
- **Documentation**: [rabbitmq-service/README.md](rabbitmq-service/README.md)

#### 12. Redis Service
- **Technology**: Redis 7.2
- **Features**:
  - Token blacklisting for JWT
  - High-performance caching
  - Session storage
  - AOF persistence
- **Documentation**: [redis-service/README.md](redis-service/README.md)

## 🛠️ Technologies

### Backend Frameworks
- **Django 5.2.7** - User, Shop, Order, Analytics services
- **FastAPI 0.115.0+** - Product, Shopcart, Wishlist, Elasticsearch, Gateway services
- **Django REST Framework 3.16.1** - REST API for Django services
- **SQLAlchemy 2.0+** - ORM for FastAPI services
- **SQLModel 0.0.22** - ORM for Wishlist service

### Databases
- **PostgreSQL 15-17** - Primary database for all services
- **Elasticsearch 8.12.1** - Full-text search engine
- **Redis 7.2** - Caching and token blacklisting

### Message Broker
- **RabbitMQ 3-management** - Event-driven communication
- **Pika 1.3.2** - Synchronous AMQP client
- **aio-pika 9.4.3+** - Asynchronous AMQP client

### Task Queue
- **Celery 5.5.3+** - Background task processing (Shopcart service)
- **Redis** - Celery backend

### Infrastructure
- **Traefik v2.10** - Reverse proxy and load balancer
- **Docker & Docker Compose** - Containerization
- **Gunicorn 23.0.0** - WSGI server for Django services
- **Uvicorn 0.30.6+** - ASGI server for FastAPI services

### Authentication & Security
- **JWT (python-jose 3.5.0)** - Token-based authentication
- **Django Authentication** - User authentication
- **CSRF Protection** - Cross-site request forgery protection
- **SQL Injection Protection** - ORM-based protection

### API Documentation
- **drf-spectacular 0.28.0** - OpenAPI schema for Django
- **FastAPI Auto Docs** - Swagger UI and ReDoc
- **drf-yasg 1.21.7+** - Alternative Swagger for Django

### Testing
- **pytest 8.4.2+** - Testing framework
- **pytest-django 4.11.1+** - Django integration for pytest

### Python Versions
- **Python 3.10+** - User, Analytics services
- **Python 3.11+** - Product, Shopcart, Wishlist, Elasticsearch services
- **Python 3.13+** - Shop, Order, Gateway services

## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.10+** (for local development)
- **PostgreSQL** (for local development, optional)
- **Git** for cloning the repository

### Quick Start with Docker

1. **Clone the repository**:
```bash
git clone <repository-url>
cd EcommerceLocal
```

2. **Start all services**:
```bash
# Start infrastructure services first
cd rabbitmq-service && docker-compose up -d
cd ../redis-service && docker-compose up -d
cd ../traefik-service && docker-compose up -d

# Start core services
cd ../gateway-service && docker-compose up -d
cd ../user-service && docker-compose up -d
cd ../shop-service && docker-compose up -d
cd ../product-service && docker-compose up -d
cd ../shopcart-service && docker-compose up -d
cd ../order-service && docker-compose up -d
cd ../wishlist-service && docker-compose up -d
cd ../analytic-service && docker-compose up -d
cd ../elasticsearch-service && docker-compose up -d
```

3. **Access the services**:
- **Gateway API**: `http://gateway.localhost`
- **API Documentation**: `http://gateway.localhost/docs`
- **Traefik Dashboard**: `http://traefik.localhost`
- **RabbitMQ Management**: `http://rabbitmq-admin.localhost`
- **Kibana**: `http://kibana-admin.localhost`

### Local Development Setup

For detailed setup instructions for each service, refer to their individual README files:

- [User Service Setup](user-service/README.md#setup--installation)
- [Shop Service Setup](shop-service/README.md#setup--installation)
- [Product Service Setup](product-service/README.md#setup--installation)
- [Order Service Setup](order-service/README.md#setup--installation)
- [Shopcart Service Setup](shopcart-service/README.md#setup--installation)
- [Wishlist Service Setup](wishlist-service/README.md#setup--installation)
- [Analytics Service Setup](analytic-service/README.md#setup--installation)
- [Elasticsearch Service Setup](elasticsearch-service/README.md#setup--installation)
- [Gateway Service Setup](gateway-service/README.md#setup--installation)

### Environment Variables

Each service requires specific environment variables. Create `.env` files in each service directory based on the examples in their respective README files.

Common environment variables:
- Database connection strings
- RabbitMQ connection details
- Service URLs for inter-service communication
- JWT secrets
- Redis connection details

## 🔄 Service Communication

### Synchronous Communication (HTTP)

Services communicate via HTTP REST APIs:

- **Gateway → Services**: Routes requests with `X-User-ID` header
- **Service → Service**: Direct HTTP calls for data fetching
- **Authentication**: Header-based (`X-User-ID` or `X-User-Id`)

### Asynchronous Communication (RabbitMQ)

Event-driven communication via RabbitMQ exchanges:

#### Event Exchanges

1. **user_events**
   - `user.created` - New user registration
   - Consumed by: Shopcart Service (auto-create cart)

2. **shop_events**
   - `shop.approved` - Shop approved
   - `shop.updated` - Shop updated
   - `shop.deleted` - Shop deleted
   - Consumed by: User Service (update shop owner status), Shopcart Service (delete cart), Elasticsearch Service (index updates)

3. **product_events**
   - `product.created` - New product
   - `product.updated` - Product updated
   - `product.deleted` - Product deleted
   - Consumed by: Elasticsearch Service (index updates)

4. **order_events**
   - `order.created` - New order
   - `order.item.created` - Order item created
   - `order.item.status.updated` - Order item status changed
   - Consumed by: Product Service (stock reduction), Shopcart Service (clear cart), Shop Service (create shop order items), Analytics Service (order processing)

5. **wishlist_events**
   - `wishlist.created` - Item added to wishlist
   - `wishlist.deleted` - Item removed from wishlist

### Event Flow Examples

#### Order Creation Flow

1. User creates order from cart → **Order Service**
2. Order Service validates stock → **Product Service** (HTTP)
3. Order Service creates order → Publishes `order.created` event
4. **Product Service** consumes event → Reduces stock
5. **Shopcart Service** consumes event → Clears cart
6. **Shop Service** consumes `order.item.created` → Creates shop order items
7. Order items reach final status → **Analytics Service** receives approved order

#### User Registration Flow

1. User registers → **User Service**
2. User Service publishes `user.created` event
3. **Shopcart Service** consumes event → Auto-creates shopping cart

#### Shop Approval Flow

1. Admin approves shop → **Shop Service**
2. Shop Service publishes `shop.approved` event
3. **User Service** consumes event → Updates `is_shop_owner` flag
4. **Shopcart Service** consumes event → Deletes user's cart (shop owners can't have carts)
5. **Elasticsearch Service** consumes event → Indexes shop for search

## 📚 API Documentation

### Unified API Documentation

The Gateway Service provides unified API documentation for all services:

- **Swagger UI**: `http://gateway.localhost/docs`
- **ReDoc**: `http://gateway.localhost/redoc`
- **OpenAPI JSON**: `http://gateway.localhost/openapi.json`

### Individual Service Documentation

Each service also provides its own API documentation:

- **User Service**: `http://user-admin.localhost/api/schema/swagger/`
- **Shop Service**: `http://shop-admin.localhost/api/schema/swagger-ui/`
- **Product Service**: `http://product-admin.localhost/docs`
- **Order Service**: `http://order-admin.localhost/api/schema/swagger-ui/`
- **Analytics Service**: `http://analytic-admin.localhost/api/schema/swagger-ui/`
- **Shopcart Service**: Check service documentation
- **Wishlist Service**: Check service documentation
- **Elasticsearch Service**: `http://elasticsearch-api.localhost/docs`

## 💻 Development

### Project Structure

```
EcommerceLocal/
├── user-service/          # User authentication and management
├── shop-service/          # Shop management
├── product-service/       # Product catalog
├── order-service/         # Order processing
├── shopcart-service/      # Shopping cart
├── wishlist-service/      # Wishlist management
├── analytic-service/      # Analytics and reporting
├── elasticsearch-service/ # Search functionality
├── gateway-service/       # API Gateway
├── traefik-service/       # Reverse proxy
├── rabbitmq-service/      # Message broker
└── redis-service/         # Caching
```

### Development Workflow

1. **Start infrastructure services** (RabbitMQ, Redis, Traefik)
2. **Start dependent services** (User, Shop, Product)
3. **Start dependent services** (Shopcart, Order, Wishlist)
4. **Start supporting services** (Analytics, Elasticsearch)
5. **Start Gateway** (last, as it depends on all services)

### Code Style

- **Django Services**: Follow Django and PEP 8 conventions
- **FastAPI Services**: Follow FastAPI and PEP 8 conventions
- **Type Hints**: Use type hints where applicable
- **Documentation**: Include docstrings for functions and classes

### Testing

Run tests for each service:

```bash
# Django services
cd user-service && python manage.py test
cd shop-service && pytest
cd order-service && pytest
cd analytic-service && pytest

# FastAPI services
cd product-service && pytest
cd shopcart-service && pytest
cd wishlist-service && pytest
cd elasticsearch-service && pytest
cd gateway-service && pytest
```

## 🚢 Deployment

### Docker Deployment

Each service includes a `docker-compose.yml` file for containerized deployment. Services are designed to work together via Docker networks.

### Production Considerations

- **Database**: Use managed PostgreSQL services (AWS RDS, Google Cloud SQL)
- **Message Broker**: Use managed RabbitMQ or cloud message queues
- **Caching**: Use managed Redis services
- **Load Balancing**: Configure Traefik for production with SSL certificates
- **Monitoring**: Set up logging and monitoring (ELK stack, Prometheus, Grafana)
- **Security**: Enable HTTPS, configure CORS, set up firewall rules
- **Scaling**: Scale services horizontally based on load

### Cloud Deployment

Some services support Google Cloud Run deployment:
- Order Service
- Shop Service

Configure `CLOUD_SQL_CONNECTION_NAME` for Cloud SQL integration.

## 🔮 Future Features

The following features are planned for future implementation (not critical but will enhance the platform):

### Payment Integration
- Payment gateway integration (Stripe, PayPal, etc.)
- Payment processing service
- Payment history and receipts
- Refund management

### Notification Service
- Email notifications (order confirmations, status updates)
- SMS notifications
- Push notifications
- In-app notifications
- Notification preferences

### Review and Rating System
- Product reviews with ratings
- Shop reviews
- Review moderation
- Review analytics

### Inventory Management
- Advanced stock management
- Low stock alerts
- Automatic reordering
- Warehouse management

### Shipping Integration
- Shipping provider integration
- Shipping cost calculation
- Tracking number management
- Delivery status updates

### Discount and Coupon System
- Coupon code management
- Discount rules and conditions
- Promotional campaigns
- Flash sales

### Multi-language Support
- Internationalization (i18n)
- Multi-language product descriptions
- Localized pricing

### Advanced Analytics
- Customer behavior analytics
- Sales forecasting
- Inventory analytics
- Marketing campaign analytics

### Admin Dashboard
- Centralized admin panel
- Shop approval workflow UI
- Order management interface
- Analytics dashboard
- User management

### Mobile App Support
- RESTful API for mobile apps
- Mobile-specific endpoints
- Push notification support

### Real-time Features
- WebSocket support for real-time updates
- Live order tracking
- Real-time inventory updates
- Chat support

### Advanced Search
- Faceted search
- Search filters
- Search suggestions
- Search analytics

### Recommendation Engine
- Product recommendations
- "Customers who bought this also bought"
- Personalized recommendations
- Trending products

## 📝 License

This project is part of the EcommerceLocal platform.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check individual service README files for service-specific documentation
- Review API documentation at the Gateway Service
- Check service logs for debugging

## 🎯 Architecture Principles

- **Microservices**: Each service handles a specific business domain
- **Event-Driven**: Asynchronous communication via RabbitMQ
- **API Gateway**: Single entry point for all client requests
- **Service Independence**: Services can be developed and deployed independently
- **Database per Service**: Each service has its own database
- **Containerization**: All services are containerized with Docker
- **Scalability**: Services can be scaled independently based on load

---

**Note**: This is a comprehensive e-commerce platform. Each service is designed to be independently deployable and scalable. For detailed information about each service, refer to their individual README files.
