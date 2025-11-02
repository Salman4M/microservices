from sqlalchemy import delete
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from .base import BaseRepository
from src.app.models.v1 import Product, ProductCategory
from src.app.schemas.v1 import ProductCreate


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db_session: Session):
        super().__init__(Product, db_session)

    def create_with_categories(self, obj_in: ProductCreate) -> Product:
        db_product = self.create(obj_in)
        # Handle many-to-many with ProductCategory
        for category_id in obj_in.categories:  # Assuming categories field in schema
            pc = ProductCategory(product_id=db_product.id, category_id=category_id)
            self.db_session.add(pc)
        self.db_session.commit()
        return db_product

    def update_with_categories(self, id: UUID, obj_in: ProductCreate) -> Optional[Product]:
        db_product = self.update(id, obj_in)
        if db_product:
            # Replace categories
            self.db_session.execute(delete(ProductCategory).where(ProductCategory.product_id == id))
            for category_id in obj_in.categories:
                pc = ProductCategory(product_id=id, category_id=category_id)
                self.db_session.add(pc)
            self.db_session.commit()
        return db_product