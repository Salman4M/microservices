from .base import BaseRepository
from src.app.models.v1 import ProductVariation
from sqlalchemy.orm import Session

class ProductVariationRepository(BaseRepository[ProductVariation]):
    def __init__(self, db: Session):
        super().__init__(ProductVariation, db)