from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.app.core.db import Base

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_variation_id = Column(UUID(as_uuid=True), ForeignKey("product_variations.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(255), nullable=False)
    alt_text = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    variation = relationship("ProductVariation", back_populates="images")