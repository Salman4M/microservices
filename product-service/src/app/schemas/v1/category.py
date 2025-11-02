from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    is_parent: bool = False

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: UUID

    products: List["Product"] = []

    class Config:
        from_attributes = True

from .product import Product  # Circular import resolution