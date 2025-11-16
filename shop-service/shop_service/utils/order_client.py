import httpx
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger('shop_service')


class OrderServiceClient:
    def __init__(self):
        self.base_url = os.getenv('ORDER_SERVICE')
        self.timeout = 30.0  # Increased timeout to allow for order processing
        
    def update_order_item_status(self, order_item_id: int, status: int, shop_owner_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Update order item status in order service
        shop_owner_user_id: Shop owner's user ID (not the customer who created the order)
        Returns the updated order item data or None if failed
        """
        try:
            url = f"{self.base_url}/api/order-items/{order_item_id}/status/"
            
            headers = {
                'Content-Type': 'application/json',
                'X-User-ID': str(shop_owner_user_id),  
            }
            
            data = {
                'status': status
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.patch(url, json=data, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(
                        f"Failed to update order item status in order service: "
                        f"status_code={response.status_code} response={response.text}"
                    )
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout while updating order item {order_item_id} status in order service")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error while updating order item status: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while updating order item status: {e}", exc_info=True)
            return None


order_client = OrderServiceClient()