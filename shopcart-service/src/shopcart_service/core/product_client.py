import httpx
import os
from typing import Optional
from fastapi import HTTPException, status
from dotenv import load_dotenv

from uuid import UUID

load_dotenv() 

PRODUCT_SERVICE = os.getenv('PRODUCT_SERVICE')


class ProductServiceDataCheck:
    def __init__(self):
        self.base_url = PRODUCT_SERVICE
        self.timeout = 30.0
    
    async def verify_product_exists(self, variation_id: UUID):
        try:
            url = f'{self.base_url}/api/products/variations/{str(variation_id)}'
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail="Product not found"
                    )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=503,
                        detail="Product service unavailable"
                    )
                
                data = response.json()
                
                # Check if product is active
                if not data.get('product', {}).get('is_active'):
                    raise HTTPException(
                        status_code=400,
                        detail="Product unavailable"
                    )
                
                return data
                    
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to product service"
            )
    #in the shopcart to check if there is enough amount of product in the stock
    async def verify_stock(self, variation_id: UUID, quantity: int):
        data = await self.verify_product_exists(variation_id)
        
        # Check stock
        available = data.get('amount', 0)
        if available < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Only {available} items available"
            )
        
        return data

product_client = ProductServiceDataCheck()
