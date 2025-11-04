import httpx
import os
from typing import List
from rest_framework.exceptions import APIException
from dotenv import load_dotenv

load_dotenv()

SHOP_SERVICE = os.getenv('SHOP_SERVICE')


class ShopServiceClient:
    def __init__(self):
        self.base_url = SHOP_SERVICE
        self.timeout = 30.0

    def get_user_shop_ids(self, user_id: str) -> List[str]:
        if not self.base_url:
            raise APIException('Shop Service configuration missing')

        url = f'{self.base_url}/api/user/{user_id}/'
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(
                    url,
                    headers={
                        'Content-Type': 'application/json',
                    }
                )

            if response.status_code == 200:
                data = response.json() or []
                ids = []
                items = []
                if isinstance(data, dict):
                    shops_val = data.get('shops')
                    if isinstance(shops_val, list):
                        items = shops_val
                    else:
                        items = [data]
                elif isinstance(data, list):
                    items = data

                for item in items:
                    if isinstance(item, str):
                        ids.append(str(item))
                    elif isinstance(item, dict):
                        shop_id = item.get('id') or item.get('shop_id') or item.get('uuid')
                        if shop_id:
                            ids.append(str(shop_id))
                return ids
            elif response.status_code == 404:
                return []
            else:
                raise APIException(f'Shop Service error: {response.status_code}')
        except httpx.RequestError as e:
            raise APIException(f'Failed to connect to Shop Service: {str(e)}')
        except Exception as e:
            raise


shop_client = ShopServiceClient()

