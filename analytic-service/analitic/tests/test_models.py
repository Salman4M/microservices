import uuid
from django.test import TestCase
from analitic.models import Shop, Product, ShopView, ProductView, AnalyticsProduct

class ShopModelTest(TestCase):
    def test_create_shop(self):
        shop = Shop.objects.create(external_id=uuid.uuid4(), name="Test Shop")
        self.assertEqual(shop.name, "Test Shop")
        self.assertIsInstance(shop.id, uuid.UUID)

class ProductModelTest(TestCase):
    def test_create_product(self):
        product = Product.objects.create(external_id=uuid.uuid4(), name="Test Product")
        self.assertEqual(product.name, "Test Product")
        self.assertIsInstance(product.id, uuid.UUID)

class ShopViewModelTest(TestCase):
    def test_create_shop_view(self):
        shop = Shop.objects.create(external_id=uuid.uuid4(), name="Test Shop")
        view = ShopView.objects.create(shop=shop)
        self.assertEqual(view.shop, shop)

class ProductViewModelTest(TestCase):
    def test_create_product_view(self):
        product = Product.objects.create(external_id=uuid.uuid4(), name="Test Product")
        view = ProductView.objects.create(product=product)
        self.assertEqual(view.product, product)

class AnalyticsProductModelTest(TestCase):
    def test_create_analytics_product(self):
        shop = Shop.objects.create(external_id=uuid.uuid4(), name="Test Shop")
        product = Product.objects.create(external_id=uuid.uuid4(), name="Test Product")

        analytics = AnalyticsProduct.objects.create(
            shop=shop.external_id,             # obyekt yox, UUID göndəririk
            product_variation=product.external_id,  # obyekt yox, UUID
            count=10,
            original_price=90,
            sale_price=100
        )

        self.assertEqual(analytics.count, 10)
        self.assertEqual(analytics.shop, shop.external_id)
        self.assertEqual(analytics.product_variation, product.external_id)
