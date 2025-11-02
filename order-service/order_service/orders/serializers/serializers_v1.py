from rest_framework import serializers

from ..models import *



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id", 
            "order", 
            "status", 
            "quantity",
            "product_variation", 
            "price"
        ]
        read_only_fields = ["id"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", 
            "user_id", 
            "created_at", 
            "is_approved",
            "items"
        ]
        read_only_fields = ["id", "created_at"]
