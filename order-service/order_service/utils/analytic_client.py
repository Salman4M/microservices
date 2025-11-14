import httpx
import os
import logging
from typing import Optional
from rest_framework.exceptions import APIException
from dotenv import load_dotenv
from django.conf import settings

logger = logging.getLogger(__name__)

load_dotenv()

ANALYTIC_SERVICE = os.getenv('ANALYTIC_SERVICE')


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

        payload = {
            'order': order.id,
            'user_id': order.user_id,
            'created_at': order.created_at.isoformat(),
            'items': list(order_items),
        }

        url = f"{self.base_url}/api/orders/"
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