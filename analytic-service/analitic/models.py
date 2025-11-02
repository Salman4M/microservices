import uuid
from django.db import models
from django.utils import timezone


# 1️⃣ Shops
class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Öz UUID id
    external_id = models.UUIDField(unique=True)  # Xarici sistemdən gələn UUID
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"{self.name} ({self.external_id})"


# 2️⃣ Products
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.UUIDField(unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"{self.name} ({self.external_id})"


# 3️⃣ ShopViews
class ShopView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Shop View - {self.shop}"


# 4️⃣ ProductViews
class ProductView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Product View - {self.product}"


# 5️⃣ AnalyticsProducts
class AnalyticsProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    product_variation = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"Analytics: {self.shop} / {self.product_variation}"
