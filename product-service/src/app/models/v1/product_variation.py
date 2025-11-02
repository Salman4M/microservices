from sqlalchemy import BigInteger, Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.app.core.db import Base

class ProductVariation(Base):
    __tablename__ = "product_variations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    size = Column(String(10), nullable=True)
    color = Column(String(30), nullable=True)
    count = Column(BigInteger, default=0)  # Retained as BigInteger for count
    amount = Column(BigInteger, default=0)  # Retained as BigInteger for stock
    amount_limit = Column(BigInteger, default=0)  # Retained as BigInteger for limit
    price = Column(Numeric(10, 2), nullable=True)
    original_price = Column(Numeric(10, 2), nullable=True)
    discount = Column(Numeric(5, 2), nullable=True)

    product = relationship("Product", back_populates="variations")
    images = relationship("ProductImage", back_populates="variation")
    comments = relationship("Comment", back_populates="variation")