from pydantic import BaseModel, Field, validator
from typing import Optional
from uuid import UUID

class CommentBase(BaseModel):
    product_variation_id: UUID = Field(..., description="ID of the associated product variation")
    rating: int = Field(..., ge=1, le=5)
    content: str = Field(..., max_length=1000)

class CommentCreate(CommentBase):
    pass

class CommentBaseWithUser(CommentBase):
    user_id: UUID = Field(..., description="ID of the user, managed by User service")

class Comment(CommentBaseWithUser):
    comment_id: UUID
    created_at: str
    is_active: bool = True

    variation: Optional["ProductVariation"] = None

    class Config:
        from_attributes = True

from .product_variation import ProductVariation  # Circular import resolution