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
    try:
        url = f'{PRODUCT_SERVICE}/api/products/variations/{str(variation_id)}'
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            logger.warning(f"Product variation {variation_id} not found")
            return None
        
        if response.status_code != 200:
            logger.error(f"Product service returned {response.status_code}")
            return None
        
        data = response.json()        
        return {
            "amount":data.get('amount',0),
            "is_active":data.get('product',{}).get('is_active',True)
        }
                
    except Exception as e:
        logger.error(f"Error fetching product variation {variation_id}: {e}")
        return None

@celery.task(name='shopcart_service.tasks.sync_cart_stock')
def sync_cart_stock():

    try:
        db: Session = SessionLocal()

        cart_items = db.query(models.CartItem).all()
        for item in cart_items:
            try:
                product_data = verify_product_exists(item.product_variation_id)
                if not product_data:
                    logger.info(
                    f"Removing item {item.id} (product {item.product_variation_id}): "
                    f"Product not found or inactive"
                    )
                    db.delete(item)
                    continue

                available_stock = product_data.get('amount',0)

                if available_stock==0:
                    logger.info(
                            f"Removing item {item.id} (product {item.product_variation_id}): "
                            f"Out of stock"
                    )
                    db.delete(item)
                    continue
                if available_stock < item.quantity:
                        old_quantity = item.quantity
                        item.quantity = available_stock
                        logger.info(
                            f"Updated item {item.id} (product {item.product_variation_id}): "
                            f"quantity {old_quantity} → {available_stock} (stock limit)"
                        )
            except Exception as e:
                logger.error(f"Error while processing cart item {item.id}: {e}")
                continue

        db.commit()

        return {
            "status":"success",
            "total_items": len(cart_items)
        }
    except Exception as e:
        logger.error(f"Fatal error in sync_cart_stock: {e}")
        db.rollback()
        return {
            'status': 'error',
            'message': str(e)
        }
    
    finally:
        db.close()
            
