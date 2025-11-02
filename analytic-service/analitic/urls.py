from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShopViewViewSet, ProductViewViewSet, AnalyticsProductViewSet

router = DefaultRouter()
router.register(r'shop-views', ShopViewViewSet, basename='shop-view')
router.register(r'product-views', ProductViewViewSet, basename='product-view')
router.register(r'analytics-products', AnalyticsProductViewSet, basename='analytics-product')

urlpatterns = [
    path('', include(router.urls)),
]
