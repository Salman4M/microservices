from fastapi import FastAPI
from src.shopcart_service.core.db import Base, engine
from src.shopcart_service.api.v1 import routes as routes_v1

# Initialize database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shopcart Service")

app.include_router(routes_v1.router, prefix="", tags=["Cart v1"])

