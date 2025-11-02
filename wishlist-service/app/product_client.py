import httpx
import os
from typing import Optional
from fastapi import HTTPException, status
from dotenv import load_dotenv


load_dotenv() 

PRODUCT_SERVICE = os.getenv('PRODUCT_SERVICE')


class ProductServiceDataCheck:
    def __init__(self):
        self.base_url = PRODUCT_SERVICE
        self.timeout = 30.0
    
    async def get_product_data_by_variation_id(self, product_variation_id: str) -> Optional[dict]:
        try:
            url = f'{self.base_url}/api/products/variations{product_variation_id}'
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={'Content-Type': 'application/json'}
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