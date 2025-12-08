import httpx
import os
from typing import Optional
from fastapi import HTTPException, status


PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://fastapi_app:8000')


class ProductServiceDataCheck:
    def __init__(self):
        self.base_url = PRODUCT_SERVICE_URL
        self.timeout = 30.0
    
    async def get_product_data_by_variation_id(self, product_var_id: str, user_id: Optional[str] = None) -> Optional[dict]:
        try:
            url = f'{self.base_url}/api/products/variations/{product_var_id}'
            
            headers = {'Content-Type': 'application/json'}
            if user_id:
                headers['X-User-ID'] = str(user_id)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=headers
                )
                
                if response.status_code == 200:
                    product_data = response.json()
                    product_id = product_data.get('id')
                    return product_id
                elif response.status_code == 404:
                    return None  
                else:
                    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f'Product Service error: {response.status_code} - {response.text}'
                    )           
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'Failed to connect to Product Service: {str(e)}'
            )

product_client = ProductServiceDataCheck()