from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import UniqueConstraint



class Wishlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    product_variation_id: Optional[str] = Field(default=None, index=True) 
    shop_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'product_variation_id', 'shop_id', 
                        name='uq_user_product_shop'),
    )


class WishlistCreate(SQLModel):
    product_variation_id: Optional[str] = None
    shop_id: Optional[str] = None


class WishlistResponse(SQLModel):
    id: int
    user_id: str
    product_variation_id: Optional[str]
    shop_id: Optional[str]
    created_at: datetime

class WishlistListResponse(SQLModel):
    items: list[WishlistResponse]