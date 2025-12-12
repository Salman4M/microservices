from .base import BaseRepository
from src.app.models.v1 import ProductVariation
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException

class ProductVariationRepository(BaseRepository[ProductVariation]):
    def __init__(self, db: Session):
        super().__init__(ProductVariation, db)

    # def decrease_amount(self, variation_id: UUID, quantity: int) -> ProductVariation: # for ordering and blocking a product(variation)
    #     variation = (
    #         self.db_session.query(ProductVariation)
    #         .filter(ProductVariation.id == variation_id)
    #         .with_for_update()  # optional for concurrency control
    #         .first()
    #     )

    #     if not variation:
    #         raise HTTPException(status_code=404, detail="Variation not found")

    #     if variation.amount < quantity:
    #         raise HTTPException(status_code=400, detail="Not enough stock available")

    #     variation.amount -= quantity
    #     self.db_session.commit()
    #     self.db_session.refresh(variation)
    #     return variation
    

    def increase_amount(self, variation_id: UUID, quantity: int) -> ProductVariation: # for restocking,non-blocking or order cancellation 
        variation = (
            self.db_session.query(ProductVariation)
            .filter(ProductVariation.id == variation_id)
            .with_for_update()
            .first()
        )

        if not variation:
            raise HTTPException(status_code=404, detail="Variation not found")

        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")

        variation.amount += quantity
        self.db_session.commit()
        self.db_session.refresh(variation)
        return variation

    def get_low_stock_items(self):
        return self.db.query(ProductVariation).filter(ProductVariation.amount <= ProductVariation.amount_limit).all()


    # Helper method to get product_id by variation_id for cache invalidation
    def get_product_id(self, variation_id: UUID):
        variation = self.db_session.query(ProductVariation).filter(ProductVariation.id == variation_id).first()

        if not variation:
            return None

        return variation.product_id


    def get_variations_by_product(self, product_id: UUID, skip: int = 0, limit: int = 100):
        return (
            self.db_session.query(ProductVariation)
            .filter(ProductVariation.product_id == product_id)
            .offset(skip)
            .limit(limit)
            .all()
        )