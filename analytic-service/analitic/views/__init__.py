from .shop_views import ShopViewViewSet
from .product_views import ProductViewViewSet
from .order_views import AnalyticsViewSet, analitic_order_completed

__all__ = [
    'ShopViewViewSet',
    'ProductViewViewSet', 
    'AnalyticsViewSet',
    'analitic_order_completed'
]