from .celery_app import celery
import os
from dotenv import load_dotenv
from uuid import UUID
import requests
from sqlalchemy.orm import Session
from .core.db import SessionLocal
from . import models
import logging

logger = logging.getLogger(__name__)
load_dotenv() 

PRODUCT_SERVICE = os.getenv('PRODUCT_SERVICE')

def verify_product_exists(variation_id: UUID):
    """
    Check product variation existence and get current stock.
    Returns dict with amount and is_active, or None if not found.
    """
    try:
        url = f'{PRODUCT_SERVICE}/api/products/variations/{str(variation_id)}'
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            logger.warning(f"⚠️ Product variation {variation_id} not found")
            return None
        
        if response.status_code != 200:
            logger.error(f"❌ Product service returned {response.status_code}")
            return None
        
        data = response.json()
        product = data.get('product', {})
        
        return {
            "amount": data.get('amount', 0),
            "is_active": product.get('is_active', True)
        }
                
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Timeout fetching product variation {variation_id}")
        return None
    except Exception as e:
        logger.error(f"❌ Error fetching product variation {variation_id}: {e}")
        return None


@celery.task(name='shopcart_service.tasks.sync_cart_stock')
def sync_cart_stock():
    """
    Periodic task to sync cart items with product stock.
    - Removes items that are out of stock or inactive
    - Adjusts quantities if stock is lower than cart quantity
    Runs every minute.
    """
    db: Session = None
    
    try:
        db = SessionLocal()
        
        # Get ALL cart items across all users
        cart_items = db.query(models.CartItem).join(
            models.ShopCart
        ).all()
        
        total_items = len(cart_items)
        logger.info(f"🔍 Sync starting - Found {total_items} cart items to check")
        
        if total_items == 0:
            logger.info("ℹ️ No cart items in database - nothing to sync")
            return {
                "status": "success",
                "total_items": 0,
                "message": "No items to process"
            }
        
        updated_count = 0
        deleted_count = 0
        unchanged_count = 0
        error_count = 0
        
        for item in cart_items:
            try:
                logger.debug(
                    f"Checking item {item.id}: "
                    f"cart={item.shop_cart_id}, "
                    f"variation={item.product_variation_id}, "
                    f"quantity={item.quantity}"
                )
                
                # Get current product data from product service
                product_data = verify_product_exists(item.product_variation_id)
                
                # Case 1: Product not found or service error
                if product_data is None:
                    logger.info(
                        f"🗑️ Removing item {item.id} "
                        f"(variation {item.product_variation_id}): "
                        f"Product not found or service unavailable"
                    )
                    db.delete(item)
                    deleted_count += 1
                    continue
                
                # Case 2: Product is inactive
                if not product_data.get('is_active', True):
                    logger.info(
                        f"🗑️ Removing item {item.id} "
                        f"(variation {item.product_variation_id}): "
                        f"Product is inactive"
                    )
                    db.delete(item)
                    deleted_count += 1
                    continue
                
                available_stock = product_data.get('amount', 0)
                
                # Case 3: Out of stock
                if available_stock == 0:
                    logger.info(
                        f"🗑️ Removing item {item.id} "
                        f"(variation {item.product_variation_id}): "
                        f"Out of stock"
                    )
                    db.delete(item)
                    deleted_count += 1
                    continue
                
                # Case 4: Stock lower than cart quantity
                if available_stock < item.quantity:
                    old_quantity = item.quantity
                    item.quantity = available_stock
                    updated_count += 1
                    logger.info(
                        f"📉 Updated item {item.id} "
                        f"(variation {item.product_variation_id}): "
                        f"quantity {old_quantity} → {available_stock} (stock limit)"
                    )
                else:
                    # Case 5: No change needed
                    unchanged_count += 1
                    logger.debug(
                        f"✓ Item {item.id} unchanged: "
                        f"quantity={item.quantity}, available={available_stock}"
                    )
                    
            except Exception as e:
                logger.error(f"❌ Error processing cart item {item.id}: {e}")
                error_count += 1
                continue
        
        # Commit all changes
        db.commit()
        
        result = {
            "status": "success",
            "total_items": total_items,
            "updated": updated_count,
            "deleted": deleted_count,
            "unchanged": unchanged_count,
            "errors": error_count
        }
        
        logger.info(
            f"✅ Sync completed - "
            f"Total: {total_items}, "
            f"Updated: {updated_count}, "
            f"Deleted: {deleted_count}, "
            f"Unchanged: {unchanged_count}, "
            f"Errors: {error_count}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Fatal error in sync_cart_stock: {e}")
        if db:
            db.rollback()
        return {
            'status': 'error',
            'message': str(e),
            'total_items': 0
        }
    finally:
        if db:
            db.close()


@celery.task(name='shopcart_service.tasks.test_db_connection')
def test_db_connection():
    """
    Test task to verify database connectivity and see cart contents.
    Use this for debugging.
    """
    db: Session = None
    
    try:
        db = SessionLocal()
        
        # Count carts and items
        cart_count = db.query(models.ShopCart).count()
        item_count = db.query(models.CartItem).count()
        
        logger.info(f"📊 Database stats: {cart_count} carts, {item_count} items")
        
        # List all carts with their items
        carts = db.query(models.ShopCart).all()
        for cart in carts:
            logger.info(f"  Cart {cart.id} (user {cart.user_uuid}): {len(cart.items)} items")
            for item in cart.items:
                logger.info(
                    f"    - Item {item.id}: "
                    f"variation={item.product_variation_id}, "
                    f"qty={item.quantity}"
                )
        
        return {
            "status": "success",
            "carts": cart_count,
            "items": item_count,
            "details": f"{cart_count} carts with {item_count} total items"
        }
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return {
            "status": "error", 
            "message": str(e)
        }
    finally:
        if db:
            db.close()