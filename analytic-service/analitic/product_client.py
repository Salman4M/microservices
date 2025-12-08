# product_client.py
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv('')

logger = logging.getLogger('analitic.product_client')


class ProductClient:
    def __init__(self):
        # Get PRODUCT_SERVICE_URL directly from environment variable
        self.base_url = os.getenv('PRODUCT_SERVICE_URL') or os.getenv('PRODUCT_SERVICE')
        if not self.base_url:
            logger.error("PRODUCT_SERVICE_URL not configured in environment variables")
        else:
            logger.info(f"ProductClient initialized with base_url: {self.base_url}")
    
    def get_product_variation_data(self, variation_id):
        if not self.base_url:
            logger.error(f"Cannot fetch product variation {variation_id}: PRODUCT_SERVICE_URL not configured")
            return None
            
        try:
            url = f"{self.base_url}/api/products/variations/{variation_id}"
            logger.info(f"Fetching product variation data from: {url}")
            response = requests.get(url, timeout=10)
            
            logger.info(f"Product service response status: {response.status_code} for variation_id={variation_id}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Product service response data keys: {list(data.keys())}")
                
                # Parse according to product variation response structure
                product = data.get("product")
                if not product:
                    logger.warning(f"Product variation {variation_id}: 'product' key not found in response. Response: {data}")
                    # If product is missing but product_id exists, use it
                    product_id = data.get("product_id")
                    if not product_id:
                        logger.error(f"Product variation {variation_id}: Neither 'product' nor 'product_id' found in response")
                        return None
                    # Return minimal data
                    result = {
                        "base_price": data.get("original_price") or data.get("price"),
                        "original_price": data.get("original_price") or data.get("price"),
                        "size": data.get("size"),
                        "color": data.get("color"),
                        "product_title": "",
                        "product_sku": "",
                        "shop_id": None,
                        "product_id": product_id,
                    }
                    logger.warning(f"Product variation {variation_id}: Using minimal data without product details")
                    return result
                
                # Return full data
                result = {
                    "base_price": data.get("original_price") or data.get("price"),
                    "original_price": data.get("original_price") or data.get("price"),
                    "size": data.get("size"),
                    "color": data.get("color"),
                    "product_title": product.get("title", ""),
                    "product_sku": product.get("sku", ""),
                    "shop_id": product.get("shop_id"),
                    "product_id": product.get("id") or data.get("product_id"),  
                }
                logger.info(f"Successfully fetched product variation {variation_id}: shop_id={result.get('shop_id')}, product_id={result.get('product_id')}, title={result.get('product_title')}")
                return result
            else:
                logger.warning(f"Product service returned {response.status_code} for variation_id={variation_id}")
                try:
                    error_data = response.json()
                    logger.warning(f"Error response: {error_data}")
                except:
                    logger.warning(f"Error response text: {response.text[:200]}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching product variation {variation_id}: {str(e)}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error fetching product variation {variation_id}: {str(e)}", exc_info=True)

        return None


product_client = ProductClient()
