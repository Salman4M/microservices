import uuid
from django.db import models
from django.utils import timezone

# -------------------------
# SHOP & PRODUCT MODELLƏRİ
# -------------------------
class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.UUIDField(unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"{self.name} ({self.external_id})"

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.UUIDField(unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"{self.name} ({self.external_id})"

# -------------------------
# SHOP VIEW & PRODUCT VIEW
# -------------------------
class ShopView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Shop View - {self.shop}"

class ProductView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Product View - {self.product}"

# -------------------------
# ORDER & ORDER ITEM MODELLƏRİ
# -------------------------
class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    order_id = models.BigIntegerField(unique=True)  # Order service-dən gələn integer id
    user_id = models.UUIDField()
    created_at = models.DateTimeField()
    is_enriched = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.order_id} - User {self.user_id}"

class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variation_id = models.UUIDField()
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Product service sahələri
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shop_id = models.UUIDField(null=True, blank=True)
    product_id = models.UUIDField(null=True, blank=True)
    product_title = models.CharField(max_length=255, blank=True)
    product_sku = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=100, blank=True, null=True,)
    color = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OrderItem {self.id} - Order {self.order.order_id}"

    class Meta:
        db_table = 'order_items'
        indexes = [
            models.Index(fields=['product_variation_id']),
            models.Index(fields=['shop_id']),
            models.Index(fields=['created_at']),
        ]
