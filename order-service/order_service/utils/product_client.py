import httpx
import os
from typing import Optional
from rest_framework.exceptions import APIException
from dotenv import load_dotenv

load_dotenv()

PRODUCT_SERVICE = os.getenv('PRODUCT_SERVICE')


class ProductServiceClient:
    def __init__(self):
        self.base_url = PRODUCT_SERVICE
        self.timeout = 30.0
    
    def get_variation(self, variation_id: str) -> Optional[dict]:
        url = f'{self.base_url}/api/products/variations/{variation_id}'
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(
                    url,
                    headers={
                        'Content-Type': 'application/json',
                    }
                )
            
            if response.status_code == 200:
                variation_data = response.json()
                return variation_data
            elif response.status_code == 404:
                return None
            else:
                raise APIException(f'Product Service error: {response.status_code}')
        except httpx.RequestError as e:
            raise APIException(f'Failed to connect to Product Service: {str(e)}')
        except Exception as e:
            raise

    def get_product(self, product_id: str) -> Optional[dict]:
        url = f'{self.base_url}/api/products/{product_id}'
        
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(
                    url,
                    headers={
                        'Content-Type': 'application/json',
                    }
                )
            
            if response.status_code == 200:
                product_data = response.json()
                return product_data
            elif response.status_code == 404:
                return None
            else:
                raise APIException(f'Product Service error: {response.status_code}')
        except httpx.RequestError as e:
            raise APIException(f'Failed to connect to Product Service: {str(e)}')
        except Exception as e:
            raise


product_client = ProductServiceClient()