from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.app.core.db import Base

class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    product_variation_id = Column(UUID(as_uuid=True), ForeignKey("product_variations.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, CheckConstraint("rating BETWEEN 1 AND 5"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    is_active = Column(Boolean, default=True)

    variation = relationship("ProductVariation", back_populates="comments")