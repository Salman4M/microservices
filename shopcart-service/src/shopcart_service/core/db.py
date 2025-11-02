from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.shopcart_service.core.config import get_settings

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
