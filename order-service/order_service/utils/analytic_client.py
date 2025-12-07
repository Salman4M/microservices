import httpx
import os
import logging
from typing import Optional
from rest_framework.exceptions import APIException
from dotenv import load_dotenv
from django.conf import settings

logger = logging.getLogger(__name__)

load_dotenv()

ANALYTIC_SERVICE = os.getenv('ANALYTIC_SERVICE') or settings.SERVICE_URLS.get('analytic')


class AnalyticServiceClient:
    def __init__(self):
        self.base_url = ANALYTIC_SERVICE
        self.timeout = 10.0

    def send_order(self, order) -> Optional[dict]:
        """Send approved order to analytics service."""
        if not self.base_url:
            logger.error("Analytic service URL not configured.")
            raise APIException("Analytic service URL missing in environment or settings.")

        order_items = order.items.filter(status=3).values(
            'id', 'order_id', 'quantity', 'product_variation', 'price'
        )

        # Convert items to proper format
        items_list = []
        for item in order_items:
            item_data = {
                'id': str(item['id']),  # Convert integer to string
                'quantity': item['quantity'],
                'product_variation': item['product_variation'],
                'price': float(item['price']) / 100.0 if item['price'] else 0.0,  # Convert from qepik to currency
            }
            items_list.append(item_data)
            logger.info(f"Order item {item['id']} prepared: variation_id={item['product_variation']}")

        payload = {
            'id': str(order.id),  # Convert integer to string
            'user_id': order.user_id,  # Already string (UUID format)
            'created_at': order.created_at.isoformat(),
            'items': items_list,
        }

        logger.info(f"Sending order {order.id} to analytics with {len(items_list)} items (only product_variation_id, shop_id/product_id will be fetched by analytics from product service)")

        url = f"{self.base_url}/api/analitic-order-completed/"
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.post(url, json=payload)
            
            if response.status_code == 201 or response.status_code == 200:
                logger.info(f"Order {order.id} successfully sent to analytics.")
                return response.json()
            else:
                logger.warning(f"Analytics service returned {response.status_code} for order {order.id}")
                raise APIException(f"Analytics service error: {response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Failed to send order {order.id} to analytics: {str(e)}")
            raise APIException(f"Failed to connect to analytics service: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while sending order {order.id}: {str(e)}")
            raise


analytic_client = AnalyticServiceClient()