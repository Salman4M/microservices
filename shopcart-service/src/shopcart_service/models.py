from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .core.db import Base
import uuid


class DateMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ShopCart(Base, DateMixin):
    __tablename__ = "shop_carts"

    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)

    items = relationship("CartItem", back_populates="shop_cart", cascade="all, delete-orphan")


class CartItem(Base, DateMixin):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    shop_cart_id = Column(Integer, ForeignKey("shop_carts.id", ondelete="CASCADE"),nullable=False)
    product_variation_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Integer, default=1)

    shop_cart = relationship("ShopCart", back_populates="items")
