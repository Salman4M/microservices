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
    'ShopCommentSerializer'
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
    user = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Shop
        fields = [
            'name',
            'about',
            'profile',
            'user',
        ]


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
    user = serializers.UUIDField(write_only=True)
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
    class Meta:
        model = ShopSocialMedia
        fields = '__all__'
    
    def create(self, validated_data):
        validated_data['shop'] = self.context.get('shop')
        return super().create(validated_data)