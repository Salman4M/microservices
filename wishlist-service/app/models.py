from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from sqlalchemy import UniqueConstraint



class Wishlist(SQLModel, table=True):
    """Main wishlist container - one per user"""
    __tablename__ = "wishlist"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True)  # One wishlist per user
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    items: List["WishlistItem"] = Relationship(back_populates="wishlist")


class WishlistItem(SQLModel, table=True):
    __tablename__ = "wishlist_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    wishlist_id: int = Field(foreign_key="wishlist.id")
    product_variation_id: Optional[str] = Field(default=None, index=True)
    shop_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    wishlist: Optional[Wishlist] = Relationship(back_populates="items")
    
    __table_args__ = (
        UniqueConstraint('wishlist_id', 'product_variation_id', 'shop_id',
                        name='uq_wishlist_product_shop'),
    )

class WishlistItemCreate(SQLModel):
    product_variation_id: Optional[str] = None
    # shop_id: Optional[str] = None



class WishlistItemRead(SQLModel):
    id: int
    product_variation_id: Optional[str] = None
    # shop_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WishlistRead(SQLModel):
    id: int
    user_id: str
    items: List[WishlistItemRead] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True