from rest_framework import serializers
from django.core.exceptions import ValidationError

from ..models import *

__all__ = [
    'ShopListSerializer',
    'ShopDetailSerializer',
    'ShopCreateUpdateSerializer',
    'ShopBranchListSerializer',
    'ShopBranchCreateUpdateSerializer',
    'ShopBranchDetailSerializer',
    'ShopMediaSerializer',
    'ShopSocialMediaSerializer',
    'ShopCommentSerializer',
    'ShopOrderItemSerializer',
    'ShopOrderItemStatusUpdateSerializer'
]

class ShopListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'id', 
            'name', 
            'slug', 
            'is_verified', 
            'is_active', 
            'profile'
        ]


class ShopDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'id',
            'name',
            'slug',
            'about',
            'profile',
            'is_verified',
            'is_active',
            'created_at',
            'updated_at',
        ]


class ShopCreateUpdateSerializer(serializers.ModelSerializer):
    profile = serializers.ImageField(required=False)
    id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)  

    class Meta:
        model = Shop
        fields = [
            'id',
            'user',
            'name',
            'about',
            'status',
            'profile',
        ]
        read_only_fields = ['user']


class ShopBranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopBranch
        fields = [
            'id',
            'name',
            'slug',
        ]


class ShopBranchDetailSerializer(serializers.ModelSerializer):
    shop = ShopListSerializer(read_only=True)

    class Meta:
        model = ShopBranch
        fields = [
            'id',
            'shop',
            'name',
            'about',
            'phone_number',
            'latitude',
            'longitude',
            'created_at',
            'updated_at',
            'slug'
        ]


class ShopBranchCreateUpdateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    
    class Meta:
        model = ShopBranch
        fields = [
            'id',
            'name',
            'about',
            'phone_number',
            'latitude',
            'longitude',
            'created_at',
            'updated_at',
        ]
    
    def create(self, validated_data):
        validated_data['shop'] = self.context.get('shop')
        return super().create(validated_data)


class ShopCommentSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ShopComment
        fields = '__all__'

    def validate(self, data):
        if not data.get('text') and not data.get('rating'):
            raise serializers.ValidationError('Comment text or rating must be provided.')
        return data
    
    def create(self, validated_data):
        shop = self.context.get('shop')
        return ShopComment.objects.create(shop=shop, **validated_data)


class ShopMediaSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = ShopMedia
        fields = '__all__'
    
    def validate_shop(self, value):
        request = self.context.get('request')
        if request and str(value.user) != str(request.user.id):
            raise serializers.ValidationError('You do not own this shop.')
        return value
    
    def validate_image(self, value):
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise ValidationError("Image size should not exceed 5 MB.")

        valid_formats = ['image/jpeg', 'image/png']
        if value.content_type not in valid_formats:
            raise ValidationError("Unsupported image format. Use JPEG or PNG.")
        
        return value
    
    def create(self, validated_data):
        validated_data['shop'] = self.context.get('shop')
        return super().create(validated_data)


class ShopSocialMediaSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ShopSocialMedia
        fields = '__all__'

    def create(self, validated_data):
        validated_data['shop'] = self.context.get('shop')
        return super().create(validated_data)


class ShopOrderItemSerializer(serializers.ModelSerializer):
    shop = ShopListSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ShopOrderItem
        fields = [
            'id',
            'shop',
            'order_id',
            'product_id',
            'product_variation',
            'quantity',
            'price',
            'status',
            'status_display',
            'user_id',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 
            'shop', 
            'order_id', 
            'product_id', 
            'product_variation',           
            'quantity', 
            'price', 
            'user_id', 
            'created_at', 
            'updated_at'
        ]


class ShopOrderItemStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopOrderItem
        fields = ['status']

    def validate_status(self, value):
        if value not in dict(ShopOrderItem.Status.choices):
            raise serializers.ValidationError('Invalid status value')
        return value
    
    def validate(self, attrs):
        extra_fields = set(attrs.keys()) - {'status'}
        if extra_fields:
            raise serializers.ValidationError(
                f'Only status field can be updated. Invalid fields: {", ".join(extra_fields)}'
            )
        
        # Check if the order item status is already DELIVERED (3)
        if self.instance and self.instance.status == ShopOrderItem.Status.DELIVERED:
            raise serializers.ValidationError(
                {'status': 'Cannot update order item status. Order item is already delivered and cannot be modified.'}
            )
        return attrs