import httpx
import os
from typing import Optional
from fastapi import HTTPException, status
from dotenv import load_dotenv


load_dotenv() 

SHOP_SERVICE = os.getenv('SHOP_SERVICE')


class ShopServiceDataCheck:
    def __init__(self):
        self.base_url = SHOP_SERVICE
        self.timeout = 30.0
    
    async def get_shop_data(self, shop_id: str) -> Optional[dict]:
        try:
            url = f'{self.base_url}/api/shops/{shop_id}/'
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    shop_data = response.json()
                    return shop_data
                elif response.status_code == 404:
                    return None  
                else:
                    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f'Shop Service error: {response.status_code} - {response.text}'
                    )           
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'Failed to connect to Shop Service: {str(e)}'
            )

shop_client = ShopServiceDataCheck()