import requests
from django.db import models
from django.conf import settings
from utils.analytic_client import analytic_client
import logging

logger = logging.getLogger(__name__)

class Order(models.Model):
    id = models.BigAutoField(primary_key=True)  # BIGSERIAL (PK)
    user_id = models.CharField(max_length=36)     # UUID field
    created_at = models.DateTimeField(auto_now_add=True)  # DEFAULT now()
    is_approved = models.BooleanField(default=False)      # DEFAULT FALSE

    # Əgər başqa servisdəki/tabloda id tutursansa ForeignKey əvəzinə BigIntegerField saxlayırıq:
  
    def check_and_approve(self):
        items = self.items.all()
        if items.exists() and all(item.status in [3, 4] for item in items):
            self.is_approved = True
            self.save()
            try:
                analytic_client.send_order(self)
            except Exception as e:
                logger.error(f"Error while sending order {self.id} to analytics: {str(e)}")
            
    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["user_id"]),
        ]

    def __str__(self):
        return f"Order#{self.pk} (user={self.user_id})"


class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)  # BIGSERIAL (PK)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        db_column="order_id",
    )  # NOT NULL REFERENCES orders(id)

    class Status(models.IntegerChoices):
        PROCESSING = 1, 'Processing'
        SHIPPED = 2, 'Shipped'
        DELIVERED = 3, 'Delivered'
        CANCELLED = 4, 'Cancelled'

    status = models.IntegerField(choices=Status.choices, default=Status.PROCESSING)
    quantity = models.IntegerField(default=1)            # INT NOT NULL DEFAULT 1
    product_variation = models.CharField(max_length=36)   # UUID field
    product_id = models.CharField(max_length=36, null=True, blank=True)  # UUID field (product service-dən)
    shop_id = models.CharField(max_length=36, null=True, blank=True)      # UUID field (product service-dən)
    price = models.BigIntegerField()                     # BIGINT NOT NULL (kuru x100 saxla: qepik)

    class Meta:
        db_table = "order_items"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"OrderItem#{self.pk} of Order#{self.order_id}"
    