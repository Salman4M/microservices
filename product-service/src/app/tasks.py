from .celery_app import celery
from .core.db import SessionLocal
from .repositories.v1.product_variation import ProductVariationRepository
# Use the public Pydantic schema so we send a typed object over the wire
from .schemas.v1.product_variation import ProductVariation as ProductVariationSchema
import logging

logger = logging.getLogger(__name__)

@celery.task(name='product_service.tasks.check_low_stock')
def check_low_stock():
    db = SessionLocal()
    try:
        repo = ProductVariationRepository(db)
        low_stock_items = repo.get_low_stock_items()

        logger.info(f" Found {len(low_stock_items)} low stock items")

        for item in low_stock_items:
            # Convert the SQLAlchemy model to the Pydantic schema (use model_validate which
            # supports building from attribute objects when the schema is configured for it).
            try:
                product_variation = ProductVariationSchema.model_validate(item)
                payload = product_variation.model_dump()  # serializable dict representation
            except Exception:
                # Fallback to minimal dict if schema conversion fails
                logger.exception("Failed to build ProductVariation schema from ORM object; sending minimal payload")
                payload = {
                    "product_variation_id": str(item.id),
                    "amount": item.amount,
                    "amount_limit": item.amount_limit,
                }

            celery.send_task(
                "analytics_service.tasks.process_low_stock",
                args=[payload]
            )
            logger.info(f" Sent low stock item {getattr(item, 'id', '<unknown>')} to analytics service")

        return f"{len(low_stock_items)} low stock items processed"

    finally:
        db.close()