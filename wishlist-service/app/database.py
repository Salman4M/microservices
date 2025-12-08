from sqlmodel import SQLModel, create_engine, Session
from app.config import DATABASE_URL


assert DATABASE_URL is not None

# Database Engine
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency for FastAPI"""
    with Session(engine) as session:
        yield session