from .base import BaseRepository
from src.app.models.v1 import Category    
from sqlalchemy.orm import Session

class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(Category, db)