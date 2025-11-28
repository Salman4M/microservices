from fastapi import FastAPI, Request
from src.app.api.v1.routes import router
from src.app.cache.backend import init_cache

app = FastAPI(
    title="Product Service",
    version="1.0.0",
    description="Manages products, categories, variations, and images.",
    debug=True,
)

app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize cache on startup using the project's cache helper."""
    await init_cache(app)

@app.get("/")
def read_root():
    return {"message": "Product Service is running 🚀"}
