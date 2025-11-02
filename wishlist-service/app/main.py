from fastapi import FastAPI
from app.database import create_db_and_tables
from app.config import PROJECT_NAME, API_V1_STR
from app.api.v1.endpoints import wishlist

app = FastAPI(
    title=PROJECT_NAME,
    description="Wishlist Microservice for E-commerce Platform",
    version="1.0.0",
)

# Include routers
app.include_router(wishlist.router, prefix=API_V1_STR)

@app.on_event("startup")
def startup_event():
    create_db_and_tables()

@app.get("/")
def root():
    return {
        "message": "Wishlist Service is running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "wishlist"}
