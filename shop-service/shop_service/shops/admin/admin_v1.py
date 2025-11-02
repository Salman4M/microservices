from django.contrib import admin
from django.utils.html import format_html

from ..models import *


__all__ = [
    'ShopAdmin',
    'ShopBranchAdmin',
    'ShopCommentAdmin',
    'ShopMediaAdmin',
    'ShopSocialMediaAdmin'
]

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_verified', 'is_active', 'created_at')
    list_filter = ('is_verified', 'is_active')
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShopBranch)
class ShopBranchAdmin(admin.ModelAdmin):
    list_display = ('shop', 'name', 'phone_number', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'shop__name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShopComment)
class ShopCommentAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'shop', 'text', 'rating', 'created_at', 'updated_at', 'is_active')
    list_filter = ('rating',)
    search_fields = ('text', 'shop__name')
    readonly_fields = ('created_at', 'updated_at')

    def user_display(self, obj):
        return obj.user.username if obj.user else f"User ID: {obj.user_id}"
    user_display.short_description = 'User'


@admin.register(ShopMedia)
class ShopMediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'image_preview', 'alt_text')
    search_fields = ('shop__name', 'alt_text')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'


@admin.register(ShopSocialMedia)
class ShopSocialMediaAdmin(admin.ModelAdmin):
    list_display = ('shop', 'media_name', 'media_url')
    search_fields = ('shop__name', 'media_name')
    list_filter = ('media_name',)
