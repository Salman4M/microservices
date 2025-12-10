from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime, timezone


class UserCreatedEvent(BaseModel):
    """Event published when a new user is created"""
    event_type: Literal["user.created"] = "user.created"
    user_uuid: str = Field(..., description="User UUID")
    email: Optional[str] = Field(None, description="User's email")
    username: Optional[str] = Field(None, description="Username")
    is_active: Optional[bool] = Field(None, description="User active status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ShopApprovedEvent(BaseModel):
    """Event published when a shop is approved (user becomes shop owner)"""
    event_type: Literal["shop.approved"] = "shop.approved"
    user_uuid: str = Field(..., description="User UUID who owns the shop")
    shop_id: str = Field(..., description="Shop ID")
    is_shop_owner: bool = Field(default=True, description="User is now a shop owner")
    shop_data: Optional[Dict[str, Any]] = Field(None, description="Shop details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WishlistCreatedEvent(BaseModel):
    """Event published when an item is added to wishlist"""
    event_type: Literal["wishlist.created"] = "wishlist.created"
    wishlist_id: int = Field(..., description="Wishlist item ID")
    user_id: str = Field(..., description="User ID")
    product_variation_id: Optional[str] = None
    shop_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WishlistDeletedEvent(BaseModel):
    """Event published when an item is removed from wishlist"""
    event_type: Literal["wishlist.deleted"] = "wishlist.deleted"
    wishlist_id: int
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)