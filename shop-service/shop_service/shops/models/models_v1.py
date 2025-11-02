import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from django.contrib.auth.models import User
from utils.abstract_models import SluggedModel
from utils.validators import not_only_whitespace


__all__ = [
    'Shop',
    'ShopMedia',
    'ShopBranch',
    'ShopSocialMedia',
    'ShopComment'
]

class Shop(SluggedModel):
    user = models.UUIDField(
        null=False,
        verbose_name='User'
    )
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )    
    name = models.CharField(
        max_length=100,
        validators=[not_only_whitespace],
        verbose_name='Shop name'
    )
    about = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        validators=[not_only_whitespace],
        verbose_name='About shop'
    )
    profile = models.ImageField(
        upload_to='shop_profiles',
        blank=True,
        null=True,
        verbose_name='Shop profile photo'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Shop verified'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Shop activity'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Shop created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Shop updated at'
    )

    class Meta:
        verbose_name_plural = 'Shops'

    def get_slug_source(self) -> str:
        return self.name

    def __str__(self):
        return self.name
 

class ShopBranch(SluggedModel):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        verbose_name='Shop'
    )
    name = models.CharField(
        max_length=100,
        validators=[not_only_whitespace],
        verbose_name='Shop branch name'
    )
    about = models.TextField(
        max_length=2000,
        null=True,
        blank=True,
        verbose_name='About shop branch'
    )
    phone_number = models.CharField(
        null=True,
        blank=True,
        verbose_name='Shop branch phone number'
    )
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='longitude'   
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is active'
    )

    class Meta:
        verbose_name_plural = 'ShopBranches'

    def get_slug_source(self) -> str:
        return self.name

    def __str__(self):
        return f'{self.shop.id}: {self.name}'


class ShopComment(models.Model):
    user = models.UUIDField(
        null=False,
        verbose_name='User'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Shop'
    )
    text = models.TextField(
        max_length=200,
        null=True,
        blank=True,
        validators=[not_only_whitespace],
        verbose_name='Comment text'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name='Comment rating(1-5)'
    )
    is_active = models.BooleanField(
        default=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Comment created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Comment updated at'
    )

    class Meta:
        verbose_name_plural = 'ShopComments'
        ordering = ('-created_at',)

    def clean(self):
        if not self.text and not self.rating:
            raise ValidationError('Comment text or rating must be provided.')

    def __str__(self):
        return f'{self.user} add comment to {self.shop.id}'
    

class ShopMedia(models.Model):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        verbose_name='Shop'
    )
    image = models.ImageField(
        upload_to='shop_media',
        null=False,
        verbose_name='Images of shop'
    )
    alt_text = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Alt text for image'
        )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Shop created at'
    )

    class Meta:
        verbose_name_plural = 'ShopMedias'
        ordering = ('-created_at',)

    def __str__(self):
        return str(self.id)
    

class ShopSocialMedia(models.Model):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE
    )
    media_name = models.CharField(
        max_length=50,
        verbose_name='Media name'
    )
    media_url = models.URLField(
        max_length=200,
        verbose_name='Media url'
    )

    class Meta:
        verbose_name_plural = 'ShopSocialMedias'

    def __str__(self):
        return f'{self.shop.id}: {self.media_name}'