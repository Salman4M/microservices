from rest_framework import serializers
from .models import ShopView, ProductView, AnalyticsProduct, Shop, Product


# --- Shop Serializer ---
class ShopSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    external_id = serializers.UUIDField()
    name = serializers.CharField()

    class Meta:
        model = Shop
        fields = ['id', 'external_id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'external_id': {'validators': []},  # unique yoxlamanı serializer səviyyəsində söndürür
        }


# --- Product Serializer ---
class ProductSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    external_id = serializers.UUIDField()
    name = serializers.CharField()

    class Meta:
        model = Product
        fields = ['id', 'external_id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'external_id': {'validators': []},
        }


# --- ShopView Serializer ---
class ShopViewSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    shop = ShopSerializer()
    viewed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ShopView
        fields = ['id', 'shop', 'viewed_at']

    def create(self, validated_data):
        shop_data = validated_data.pop('shop')

        # Mövcud Shop-u tap və ya yarat
        shop, _ = Shop.objects.get_or_create(
            external_id=shop_data['external_id'],
            defaults={'name': shop_data['name']}
        )

        # Hər baxış üçün yeni ShopView əlavə olunur
        shop_view = ShopView.objects.create(shop=shop)
        return shop_view


# --- ProductView Serializer ---
class ProductViewSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    product = ProductSerializer()
    viewed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ProductView
        fields = ['id', 'product', 'viewed_at']

    def create(self, validated_data):
        product_data = validated_data.pop('product')

        # Mövcud Product-u tap və ya yarat
        product, _ = Product.objects.get_or_create(
            external_id=product_data['external_id'],
            defaults={'name': product_data['name']}
        )

        # Hər baxış üçün yeni ProductView əlavə olunur
        product_view = ProductView.objects.create(product=product)
        return product_view


# --- AnalyticsProduct Serializer ---
class AnalyticsProductSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    shop = serializers.UUIDField()
    product_variation = serializers.UUIDField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = AnalyticsProduct
        fields = ['id', 'shop', 'product_variation', 'count', 'original_price', 'sale_price', 'created_at']

    def create(self, validated_data):
        shop_uuid = validated_data.pop('shop')
        product_uuid = validated_data.pop('product_variation')

        # UUID yoxdursa avtomatik yaradılır
        shop, _ = Shop.objects.get_or_create(external_id=shop_uuid, defaults={'name': f"Shop {shop_uuid}"})
        product, _ = Product.objects.get_or_create(external_id=product_uuid, defaults={'name': f"Product {product_uuid}"})

        analytics = AnalyticsProduct.objects.create(
            shop=shop,
            product_variation=product,
            **validated_data
        )
        return analytics
