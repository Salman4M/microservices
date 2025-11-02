from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class ProductVariationBase(BaseModel):
    product_id: UUID = Field(..., description="ID of the associated product")
    size: Optional[str] = Field(None, max_length=10)
    color: Optional[str] = Field(None, max_length=30)
    count: int = 0
    amount: int = 0
    amount_limit: int = 0
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    discount: Optional[float] = Field(None, ge=0, le=100)

class ProductVariationCreate(ProductVariationBase):
    pass

class ProductVariation(ProductVariationBase):
    id: UUID

    product: Optional["Product"] = None
    images: List["ProductImage"] = []
    comments: List["Comment"] = []

    class Config:
        from_attributes = True

from .product import Product
from .product_image import ProductImage
from .comment import Comment  # Circular import resolution