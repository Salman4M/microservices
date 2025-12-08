def main():
    print("Hello from ecommerce-analitic-service!")


if __name__ == "__main__":
    main()
# gateway/main.py
from fastapi import FastAPI

# Router-ləri import et
from routers.order_routes import router as orders_router
from routers.analytics_routes import router as analytics_router
from routers.product_views_routes import router as product_views_router
from routers.shop_views_routes import router as shop_views_router

app = FastAPI(title="Ecommerce Gateway", version="1.0")

# Router-ləri əlavə et
app.include_router(orders_router)
app.include_router(analytics_router)
app.include_router(product_views_router)
app.include_router(shop_views_router)

# Health check endpoint
@app.get("/health/", tags=["Health"])
async def health_check():
    return {"status": "ok"}
