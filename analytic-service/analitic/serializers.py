# serializers.py - TAM VERSİYA
import uuid
from rest_framework import serializers
from .models import ShopView, ProductView, Order, OrderItem, Shop, Product

# -----------------------------
# SHOP VIEW SERIALIZER
# -----------------------------
class ShopViewInputSerializer(serializers.Serializer):
    shop_uuid = serializers.UUIDField()
    shop_name = serializers.CharField(max_length=100)

    def create(self, validated_data):
        shop_uuid = validated_data.get("shop_uuid")
        shop_name = validated_data.get("shop_name")

        # Shop-u tap və ya yarat
        shop, created = Shop.objects.get_or_create(
            external_id=shop_uuid,
            defaults={"name": shop_name}
        )

        # Əgər mövcud shop-un adı fərqlidirsə, yenilə
        if not created and shop.name != shop_name:
            shop.name = shop_name
            shop.save()

        # ShopView yarat
        shop_view = ShopView.objects.create(shop=shop)
        return shop_view

# -----------------------------
# PRODUCT VIEW SERIALIZER
# -----------------------------
class ProductViewInputSerializer(serializers.Serializer):
    product_uuid = serializers.UUIDField()
    product_name = serializers.CharField(max_length=100)

    def create(self, validated_data):
        product_uuid = validated_data.get("product_uuid")
        product_name = validated_data.get("product_name")

        # Product-u tap və ya yarat
        product, created = Product.objects.get_or_create(
            external_id=product_uuid,
            defaults={"name": product_name}
        )

        # Əgər mövcud product-un adı fərqlidirsə, yenilə
        if not created and product.name != product_name:
            product.name = product_name
            product.save()

        # ProductView yarat
        product_view = ProductView.objects.create(product=product)
        return product_view

# -----------------------------
# PRODUCT VIEW SERIALIZER (READ)
# -----------------------------
class ProductViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductView
        fields = '__all__'

# -----------------------------
# SHOP VIEW SERIALIZER (READ)
# -----------------------------
class ShopViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopView
        fields = '__all__'

# -----------------------------
# ORDER SERIALIZER
# -----------------------------
class OrderItemReceiveSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    order = serializers.UUIDField()
    quantity = serializers.IntegerField()
    product_variation = serializers.UUIDField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    base_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        default=1.00
    )

class OrderReceiveSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    items = OrderItemReceiveSerializer(many=True)

# -----------------------------
# STATISTICS SERIALIZERS
# -----------------------------
class ProductViewStatsSerializer(serializers.Serializer):
    total_views = serializers.IntegerField()
    popular_products = serializers.ListField()

class ShopViewStatsSerializer(serializers.Serializer):
    total_views = serializers.IntegerField()
    popular_shops = serializers.ListField()

class OrderStatsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)