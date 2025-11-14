from celery_app import celery
import httpx
import os
from typing import Optional
from fastapi import HTTPException, status
from dotenv import load_dotenv
from uuid import UUID
import requests

load_dotenv() 

PRODUCT_SERVICE = os.getenv('PRODUCT_SERVICE')

@celery.task
class CartProductServiceDataCheck:
    def __init__(self):
        self.base_url = PRODUCT_SERVICE
        self.timeout = 30.0
    
    async def get_items(self):
        items = requests.get("http://shopcart_service:8000/shopcart/api/mycart")
        if not items:
            pass
        return items
    
    async def verify_product_exists(self, variation_id: UUID):
        shopcart_data = self.get_items()
        # cart_id = shopcart_data.get('id')
        items = shopcart_data.all('items', [])
        for every in items:
            variation_id = every.get('product_variation_id')
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
        data = await self.verify_prodcut_exists(variation_id)
        cart_data = self.get_items()
        cart_items = cart_data.all('items',[])
        for item in cart_items:
            if item.quantity > data.get('amount'):
                item.quantity = data.get('amount')
                item.quantity.save()
        
        return cart_items

shopcart_client = CartProductServiceDataCheck()