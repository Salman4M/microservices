# src/app/repositories/v1/product.py
from sqlalchemy import delete, and_
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from .base import BaseRepository
from src.app.models.v1 import Product, ProductCategory, Category
from src.app.schemas.v1 import ProductCreate, ProductBase


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db_session: Session):
        super().__init__(Product, db_session)

    def create_with_categories(self, obj_in: ProductCreate, shop_id: UUID) -> Product:
        category_ids = obj_in.category_ids or []
        
        # Verify that all categories exist before proceeding
        if category_ids:
            existing_categories = self.db_session.query(Category).filter(
                Category.id.in_(category_ids)
            ).all()
            existing_category_ids = {str(cat.id) for cat in existing_categories}
            missing_categories = set(str(cid) for cid in category_ids) - existing_category_ids
            
            if missing_categories:
                raise ValueError(f"Categories with IDs {missing_categories} do not exist")
        
        # Remove category_ids from dict and add shop_id
        clean_data = obj_in.dict(exclude={"category_ids"})
        clean_data["shop_id"] = shop_id
        
        # Create product with all needed data
        db_product = super().create(clean_data)
        
        for category_id in category_ids:
            pc = ProductCategory(product_id=db_product.id, category_id=category_id)
            self.db_session.add(pc)
        self.db_session.commit()
        return db_product

    def update_with_categories(self, id: UUID, obj_in: ProductCreate) -> Optional[Product]:
        category_ids = obj_in.category_ids or []
        
        # Get existing product to maintain shop_id
        existing_product = super().get(id)
        if not existing_product:
            return None
            
        # Verify that all categories exist before proceeding
        if category_ids:
            existing_categories = self.db_session.query(Category).filter(
                Category.id.in_(category_ids)
            ).all()
            existing_category_ids = {str(cat.id) for cat in existing_categories}
            missing_categories = set(str(cid) for cid in category_ids) - existing_category_ids
            
            if missing_categories:
                raise ValueError(f"Categories with IDs {missing_categories} do not exist")
        
        # Get only SET fields from ProductCreate and maintain shop_id
        clean_data = obj_in.dict(exclude={"category_ids"}, exclude_unset=True)
        clean_data["shop_id"] = existing_product.shop_id
        
        # Update product data
        db_product = super().update(id, clean_data)
        
        if not db_product:
            return None
        
        # Replace categories
        self.db_session.execute(delete(ProductCategory).where(ProductCategory.product_id == id))
        for category_id in category_ids:
            pc = ProductCategory(product_id=id, category_id=category_id)
            self.db_session.add(pc)
        self.db_session.commit()
        return db_product

    def get_categories_for_product(self, product_id: UUID) -> List[Category]:
        return self.db_session.query(Category).join(
            ProductCategory,
            ProductCategory.category_id == Category.id
        ).filter(ProductCategory.product_id == product_id).all()

    def add_category(self, product_id: UUID, category_id: UUID) -> bool:
        existing = self.db_session.query(ProductCategory).filter(
            and_(ProductCategory.product_id == product_id, ProductCategory.category_id == category_id)
        ).first()
        if existing:
            return False
        pc = ProductCategory(product_id=product_id, category_id=category_id)
        self.db_session.add(pc)
        self.db_session.commit()
        return True
        
    def remove_category(self, product_id: UUID, category_id: UUID) -> bool:
        pc = self.db_session.query(ProductCategory).filter(
            and_(ProductCategory.product_id == product_id, ProductCategory.category_id == category_id)
        ).first()
        if pc:
            self.db_session.delete(pc)
            self.db_session.commit()
            return True
        return False

    def get_products_in_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.db_session.query(Product).join(
            ProductCategory,
            ProductCategory.product_id == Product.id
        ).filter(ProductCategory.category_id == category_id).offset(skip).limit(limit).all()