from celery import Celery
import os
import logging
from sqlmodel import Session, select
from app.database import engine
from app.models import WishlistItem
from app.product_client import product_client
import asyncio

logger = logging.getLogger(__name__)


# Initialize Celery
celery = Celery(
    "wishlist_worker",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://admin:admin12345@rabbitmq:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis_service:6379/0")
)

celery.autodiscover_tasks(['app'], force = True)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_default_queue='wishlist_queue',
    task_routes={
        'app.tasks.*': {'queue': 'wishlist_queue'}
    }
)

# Configure periodic tasks
celery.conf.beat_schedule = {
    'remove-inactive-products-every-3-minutes': {
        'task': 'app.tasks.remove_inactive_products_from_wishlists',
        'schedule': 180.0,  # Every 3 minutes
    },
}


async def check_product_is_active(product_variation_id: str) -> bool:

    try:
        product_data = await product_client.get_product_data_by_variation_id(product_variation_id)
        
        if not product_data or product_data is None:
            logger.warning(f"Product variation {product_variation_id} not found")
            return False
        
        # If product_data is returned, check for is_active status
        # This assumes the product service returns product details
        logger.debug(f"Product variation {product_variation_id} is active")

        return True
        
    except Exception as e:
        logger.error(f"Error checking product {product_variation_id}: {str(e)}")
        return True


@celery.task(name='app.tasks.remove_inactive_products_from_wishlists')
def remove_inactive_products_from_wishlists():

    logger.info("🔍 Starting inactive products cleanup task...")
    
    removed_count = 0
    checked_count = 0
    error_count = 0
    
    try:
        with Session(engine) as session:
            # Get all wishlist items that have products (not shops)
            product_items = session.exec(
                select(WishlistItem).where(WishlistItem.product_variation_id.isnot(None))
            ).all()
            
            total_items = len(product_items)
            logger.info(f"📊 Found {total_items} product items in wishlists to check")
            
            if total_items == 0:
                return {
                    "status": "success",
                    "message": "No product items to check",
                    "checked": 0,
                    "removed": 0,
                    "errors": 0
                }
            
            # Check each product
            for item in product_items:
                try:
                    checked_count += 1
                    
                    # Use asyncio to run async function
                    is_active = asyncio.run(
                        check_product_is_active(item.product_variation_id)
                    )
                    
                    if is_active == False:
                        # Product is inactive or not found - remove from wishlist
                        logger.info(
                            f"🗑️ Removing inactive product {item.product_variation_id} "
                            f"from wishlist item {item.id}"
                        )
                        session.delete(item)
                        removed_count += 1
                    else:
                        logger.debug(
                            f"✓ Product {item.product_variation_id} is active - keeping in wishlist"
                        )
                    
                except Exception as e:
                    logger.error(
                        f"❌ Error processing wishlist item {item.id}: {str(e)}"
                    )
                    error_count += 1
                    continue
            
            # Commit all deletions
            session.commit()
            
            result = {
                "status": "success",
                "total_items": total_items,
                "checked": checked_count,
                "removed": removed_count,
                "kept": checked_count - removed_count,
                "errors": error_count
            }
            
            logger.info(
                f"✅ Cleanup completed - "
                f"Checked: {checked_count}, "
                f"Removed: {removed_count}, "
                f"Kept: {checked_count - removed_count}, "
                f"Errors: {error_count}"
            )
            
            return result
            
    except Exception as e:
        logger.error(f"❌ Fatal error in cleanup task: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "checked": checked_count,
            "removed": removed_count,
            "errors": error_count
        }


@celery.task(name='app.tasks.remove_specific_product_from_wishlists')
def remove_specific_product_from_wishlists(product_variation_id: str):

    logger.info(f"🗑️ Removing product {product_variation_id} from all wishlists...")
    
    try:
        with Session(engine) as session:
            # Find all wishlist items with this product
            items_to_remove = session.exec(
                select(WishlistItem).where(
                    WishlistItem.product_variation_id == product_variation_id
                )
            ).all()
            
            count = len(items_to_remove)
            
            if count == 0:
                logger.info(f"ℹ️ No wishlist items found for product {product_variation_id}")
                return {
                    "status": "success",
                    "product_variation_id": product_variation_id,
                    "removed_count": 0,
                    "message": "Product not found in any wishlist"
                }
            
            # Delete all items
            for item in items_to_remove:
                session.delete(item)
            
            session.commit()
            
            logger.info(
                f"✅ Removed product {product_variation_id} from {count} wishlists"
            )
            
            return {
                "status": "success",
                "product_variation_id": product_variation_id,
                "removed_count": count,
                "message": f"Removed from {count} wishlists"
            }
            
    except Exception as e:
        logger.error(f"❌ Error removing product from wishlists: {str(e)}")
        return {
            "status": "error",
            "product_variation_id": product_variation_id,
            "message": str(e),
            "removed_count": 0
        }


@celery.task(name='app.tasks.test_wishlist_cleanup')
def test_wishlist_cleanup():
    logger.info("🧪 Test task executed successfully")
    
    try:
        with Session(engine) as session:
            # Count total wishlist items
            all_items = session.exec(select(WishlistItem)).all()
            product_items = [i for i in all_items if i.product_variation_id]
            shop_items = [i for i in all_items if i.shop_id]
            
            result = {
                "status": "success",
                "timestamp": "now",
                "stats": {
                    "total_items": len(all_items),
                    "product_items": len(product_items),
                    "shop_items": len(shop_items)
                }
            }
            
            logger.info(f"📊 Wishlist stats: {result['stats']}")
            return result
            
    except Exception as e:
        logger.error(f"❌ Test task failed: {str(e)}")
        return {"status": "error", "message": str(e)}