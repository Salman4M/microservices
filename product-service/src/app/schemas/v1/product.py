from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

from sqlalchemy import DateTime

class ProductBase(BaseModel):
    title: str = Field(..., max_length=100)
    about: Optional[str] = Field(None, max_length=1000)
    on_sale: bool = False
    is_active: bool = True
    top_sale: bool = False
    top_popular: bool = False
    sku: Optional[str] = Field(None, max_length=50)
    base_price: float = Field(..., gt=0)

class ProductCreate(ProductBase):
    category_ids: Optional[List[UUID]] = None

class ProductInDB(ProductBase):
    shop_id: UUID = Field(..., description="ID of the shop, managed by User service")
    

class ProductUpdate(ProductBase):
    # All fields OPTIONAL for partial updates
    title: Optional[str] = Field(None, max_length=100)
    about: Optional[str] = Field(None, max_length=1000)
    on_sale: Optional[bool] = None
    is_active: Optional[bool] = None
    top_sale: Optional[bool] = None
    top_popular: Optional[bool] = None
    sku: Optional[str] = Field(None, max_length=50)
    base_price: Optional[float] = Field(None, gt=0)
    category_ids: Optional[List[UUID]] = None  # ← OPTIONAL FOR UPDATE

class Product(ProductBase): 
    id: UUID
    shop_id: Optional[UUID] = None
    created_at: datetime

#    categories: List["Category"] = []

    class Config:
        from_attributes = True

    # from .category import Category