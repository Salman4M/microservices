from django.contrib import admin
from .models import Shop, Product, ShopView, ProductView, AnalyticsProduct

# 1️⃣ Shop admin
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name')
    search_fields = ('name', 'external_id')


# 2️⃣ Product admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name')
    search_fields = ('name', 'external_id')


# 3️⃣ ShopView admin
@admin.register(ShopView)
class ShopViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('shop__name',)


# 4️⃣ ProductView admin
@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('product__name',)


# 5️⃣ AnalyticsProduct admin
@admin.register(AnalyticsProduct)
class AnalyticsProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'product_variation', 'count', 'original_price', 'sale_price', 'created_at')
    list_filter = ('shop', 'created_at')
    search_fields = ('shop__name', 'product_variation__name')
