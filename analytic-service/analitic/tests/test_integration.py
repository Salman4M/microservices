import uuid
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from analitic.models import Shop, Product, ShopView, ProductView, AnalyticsProduct


class AnalyticsProductIntegrationTest(APITestCase):
    def test_create_analytics_product_full_flow(self):
        # Lazımi obyektləri yaradın
        shop_id = uuid.uuid4()
        product_id = uuid.uuid4()

        shop = Shop.objects.create(external_id=shop_id, name="Test Shop")
        product = Product.objects.create(external_id=product_id, name="Test Product")

        data = {
            "shop": str(shop_id),
            "product_variation": str(product_id),
            "count": 5,
            "original_price": 70,
            "sale_price": 100
        }
        url = reverse('analytics-product-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # DB yoxlaması UUID-lərlə
        analytics = AnalyticsProduct.objects.get(shop=shop_id, product_variation=product_id)
        self.assertEqual(analytics.count, 5)
        self.assertEqual(analytics.original_price, 70)
        self.assertEqual(analytics.sale_price, 100)
