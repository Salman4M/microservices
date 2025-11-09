from fastapi import FastAPI, Request
from src.app.api.v1.routes import router

app = FastAPI(
    title="Product Service",
    version="1.0.0",
    description="Manages products, categories, variations, and images.",
    debug=True,
)

app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Product Service is running 🚀"}

# Add this metrics endpoint
@app.get("/metrics")
def metrics():
    """Basic metrics endpoint for Prometheus"""
    return {
        "service": "product-service",
        "status": "healthy",
        "uptime": "running"
    }