import uuid
from django.test import TestCase
from analitic.models import Shop, Product, ShopView, ProductView, AnalyticsProduct
from analitic.serializers import ShopSerializer, ProductSerializer, ShopViewSerializer, ProductViewSerializer, AnalyticsProductSerializer

class ShopSerializerTest(TestCase):
    def test_shop_serializer_create(self):
        external_id = uuid.uuid4()
        data = {"external_id": external_id, "name": "My Shop"}
        serializer = ShopSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        shop = serializer.save()
        self.assertEqual(shop.name, "My Shop")

class ProductSerializerTest(TestCase):
    def test_product_serializer_create(self):
        external_id = uuid.uuid4()
        data = {"external_id": external_id, "name": "My Product"}
        serializer = ProductSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save()
        self.assertEqual(product.name, "My Product")
