import uuid
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from analitic.models import Shop, Product

class ShopViewAPITest(APITestCase):
    def test_create_shop_view(self):
        external_id = uuid.uuid4()
        data = {
            "shop": {"external_id": str(external_id), "name": "Test Shop"}
        }
        url = reverse('shop-view-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['shop']['name'], "Test Shop")

class ProductViewAPITest(APITestCase):
    def test_create_product_view(self):
        external_id = uuid.uuid4()
        data = {
            "product": {"external_id": str(external_id), "name": "Test Product"}
        }
        url = reverse('product-view-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product']['name'], "Test Product")
