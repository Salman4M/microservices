from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ProductImageBase(BaseModel):
    product_variation_id: UUID = Field(..., description="ID of the associated product variation")
    image_url: str = Field(..., max_length=255)
    alt_text: Optional[str] = Field(None, max_length=100)

class ProductImageCreate(ProductImageBase):
    pass

class ProductImage(ProductImageBase):
    id: UUID
    created_at: str

    variation: Optional["ProductVariation"] = None

    class Config:
        from_attributes = True

from .product_variation import ProductVariation  # Circular import resolution