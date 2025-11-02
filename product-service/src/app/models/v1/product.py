import uuid
from sqlalchemy import UUID, Column, BigInteger, String, Text, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.app.core.db import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID, nullable=True) 
    title = Column(String(100), nullable=False)
    about = Column(Text, nullable=True)
    on_sale = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    top_sale = Column(Boolean, default=False)
    top_popular = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    sku = Column(String(50), unique=True)
    base_price = Column(Numeric(10, 2), nullable=False)

    categories = relationship("Category", secondary="product_categories")
    variations = relationship("ProductVariation", back_populates="product")