from django.contrib import admin

from ..models import *

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("user_id",)
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "quantity", "product_variation", "price")
    list_filter = ("status",)
    search_fields = ("order__id", "product_variation")
