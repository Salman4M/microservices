# admin.py - TAM VERSİYA
from django.contrib import admin
from .models import Shop, Product, ShopView, ProductView, Order, OrderItem

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

# 5️⃣ Order admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user_id', 'created_at', 'is_enriched')
    list_filter = ('is_enriched', 'created_at')
    search_fields = ('order_id', 'user_id')
    readonly_fields = ('created_at',)

# 6️⃣ OrderItem admin
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'order', 'product_variation_id', 'quantity', 
        'price', 'base_price', 'original_price', 'shop_id', 
        'product_id', 'product_title', 'product_sku', 'size', 'color'
    )
    list_filter = ('order__order_id',)
    search_fields = ('id', 'product_variation_id', 'product_sku', 'product_title')
    readonly_fields = ('order',)
