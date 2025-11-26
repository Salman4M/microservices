import httpx
import os
import logging
from typing import Optional, Dict
from rest_framework import status
from rest_framework.exceptions import APIException
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

SHOPCART_SERVICE = os.getenv('SHOPCART_SERVICE')


class ShopCartServiceDataCheck:
    def __init__(self):
        self.base_url = SHOPCART_SERVICE
        self.timeout = 30.0
    
    def get_shopcart_data(self, user_uuid: str) -> Optional[dict]:
        url = f'{self.base_url}/api/mycart/'
        
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(
                    url,
                    headers={
                        'Content-Type': 'application/json',
                        'X-User-ID': user_uuid
                    }
                )
            
            if response.status_code == 200:
                cart_data = response.json()
                cart_id = cart_data.get('id')
                logger.info(f'Shopcart data retrieved successfully - Cart ID: {cart_id}, User: {user_uuid}')
                return cart_data
            elif response.status_code == 404:
                logger.warning(f'No shopcart found for user: {user_uuid}')
                return None
            else:
                logger.error(f'Shopcart service error - Status: {response.status_code}, User: {user_uuid}')
                raise APIException(f'Shopcart Service error: {response.status_code}')
        except httpx.RequestError as e:
            logger.error(f'Failed to connect to Shopcart Service - User: {user_uuid}, Error: {str(e)}')
            raise APIException(f'Failed to connect to Shopcart Service: {str(e)}')
        except Exception as e:
            logger.error(f'Unexpected error in shopcart request - User: {user_uuid}, Error: {str(e)}')
            raise
    
    def update_cart_item(self, cart_item_id: int, quantity: int, user_id: str) -> bool:
        """Update cart item quantity"""
        url = f'{self.base_url}/api/items/{cart_item_id}'
        
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.put(
                    url,
                    json={'quantity': quantity},
                    headers={
                        'Content-Type': 'application/json',
                        'X-User-ID': user_id
                    }
                )
            
            if response.status_code == 200:
                logger.info(f'✅ Updated cart item {cart_item_id} to quantity {quantity}')
                return True
            else:
                logger.error(f'❌ Failed to update cart item {cart_item_id}: {response.status_code}')
                return False
                
        except Exception as e:
            logger.error(f'❌ Error updating cart item {cart_item_id}: {e}')
            return False
    
    def delete_cart_item(self, cart_item_id: int, user_id: str) -> bool:
        """Delete cart item"""
        url = f'{self.base_url}/api/items/{cart_item_id}'
        
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.delete(
                    url,
                    headers={
                        'Content-Type': 'application/json',
                        'X-User-ID': user_id
                    }
                )
            
            if response.status_code in [200, 204]:
                logger.info(f'✅ Deleted cart item {cart_item_id}')
                return True
            else:
                logger.error(f'❌ Failed to delete cart item {cart_item_id}: {response.status_code}')
                return False
                
        except Exception as e:
            logger.error(f'❌ Error deleting cart item {cart_item_id}: {e}')
            return False


shopcart_client = ShopCartServiceDataCheck()



#///// KEEP IT HERE (for myself. I'm doing it by gateway not directly)


# order-service/order_service/utils/shopcart_client.py
# from typing import  Dict
# GATEWAY_URL = os.getenv('GATEWAY_URL')


# GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://gateway_service:8080')


# class ShopCartClient:
#     """Client to communicate with ShopCart service through Gateway"""
    
#     def __init__(self):
#         self.gateway_url = GATEWAY_URL
#         self.timeout = 30.0
    
#     async def get_user_cart(self, user_uuid: str, auth_token: str) -> Optional[Dict]:
#         """
#         Get user's shopping cart from shopcart service via gateway
#         Returns cart data or None if not found
#         Raises Exception on errors
#         """
#         try:
#             url = f'{self.gateway_url}/cart/shopcart/api/mycart'
            
#             async with httpx.AsyncClient(timeout=self.timeout) as client:
#                 response = await client.get(
#                     url,
#                     headers={
#                         'Authorization': f'Bearer {auth_token}',
#                         'Content-Type': 'application/json',
#                     }
#                 )
                
#                 if response.status_code == 200:
#                     return response.json()
#                 elif response.status_code == 404:
#                     return None
#                 else:
#                     raise Exception(
#                         f'ShopCart Service error: {response.status_code} - {response.text}'
#                     )
                    
#         except httpx.RequestError as e:
#             raise Exception(f'Failed to connect to Gateway/ShopCart Service: {str(e)}')
#         except httpx.HTTPStatusError as e:
#             raise Exception(f'ShopCart Service error: {e.response.status_code} - {e.response.text}')
    
#     async def validate_cart_items(self, cart_data: Dict) -> bool:
#         """
#         Validate that cart has items and they're valid
#         """
#         if not cart_data:
#             return False
            
#         items = cart_data.get('items', [])
#         if not items:
#             return False
        
#         # Check each item has required fields
#         for item in items:
#             if not all(k in item for k in ['product_variation_id', 'quantity']):
#                 return False
        
#         return True


# # Singleton instance
# shopcart_client = ShopCartClient()
