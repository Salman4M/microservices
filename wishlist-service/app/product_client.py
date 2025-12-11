import httpx
import os
from typing import Optional
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://fastapi_app:8000')


class ProductServiceDataCheck:
    def __init__(self):
        self.base_url = PRODUCT_SERVICE_URL
        self.timeout = 30.0
    
    async def get_product_data_by_variation_id(
        self, 
        product_var_id: str, 
        user_id: Optional[str] = None
    ) -> Optional[dict]:

        try:
            url = f'{self.base_url}/api/products/variations/{product_var_id}'
            
            headers = {'Content-Type': 'application/json'}
            if user_id:
                headers['X-User-ID'] = str(user_id)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    product_data = response.json()
                    
                    # Check if product is active
                    product = product_data.get('product') or {}
                    is_active = product.get('is_active', True)
                    
                    if not is_active:
                        logger.warning(
                            f"Product variation {product_var_id} exists but is inactive"
                        )
                        return None
                    
                    return product_data
                    
                elif response.status_code == 404:
                    logger.warning(f"Product variation {product_var_id} not found")
                    return None
                    
                else:
                    logger.error(
                        f"Product Service error: {response.status_code} - {response.text}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f'Product Service error: {response.status_code}'
                    )
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to Product Service")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Product Service timeout'
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Product Service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'Failed to connect to Product Service: {str(e)}'
            )
    
    async def check_product_is_active(self, product_var_id: str) -> bool:

        try:
            url = f'{self.base_url}/api/products/variations/{product_var_id}'
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    product_data = response.json()
                    product = product_data.get('product', {})
                    is_active = product.get('is_active', True)
                    return is_active
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking product status: {str(e)}")
            return False

product_client = ProductServiceDataCheck()