from .base import BaseRepository
from src.app.models.v1 import ProductVariation
from sqlalchemy.orm import Session
from uuid import UUID


class ProductVariationRepository(BaseRepository[ProductVariation]):
    def __init__(self, db: Session):
        super().__init__(ProductVariation, db)


    def get_variations_by_product(self, product_id: UUID, skip: int = 0, limit: int = 100):
        return (
            self.db_session.query(ProductVariation)
            .filter(ProductVariation.product_id == product_id)
            .offset(skip)
            .limit(limit)
            .all()
        )