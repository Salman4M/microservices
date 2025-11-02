from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import ShopView, ProductView, AnalyticsProduct
from .serializers import ShopViewSerializer, ProductViewSerializer, AnalyticsProductSerializer

# --- ShopView ---
class ShopViewViewSet(viewsets.ModelViewSet):
    queryset = ShopView.objects.all()
    serializer_class = ShopViewSerializer

    # GET /shop-views/count/
    @action(detail=False, methods=['get'])
    def count(self, request):
        data = ShopView.objects.values(
            'shop__external_id', 'shop__name'
        ).annotate(view_count=Count('id'))
        return Response(data)

# --- ProductView ---
class ProductViewViewSet(viewsets.ModelViewSet):
    queryset = ProductView.objects.all()
    serializer_class = ProductViewSerializer

    # GET /product-views/count/
    @action(detail=False, methods=['get'])
    def count(self, request):
        data = ProductView.objects.values(
            'product__external_id', 'product__name'
        ).annotate(view_count=Count('id'))
        return Response(data)

# --- AnalyticsProduct ---
class AnalyticsProductViewSet(viewsets.ModelViewSet):
    queryset = AnalyticsProduct.objects.all()
    serializer_class = AnalyticsProductSerializer

    # Optional: total count per shop + product
    @action(detail=False, methods=['get'])
    def count(self, request):
        data = AnalyticsProduct.objects.values(
            'shop__external_id', 'shop__name',
            'product_variation__external_id', 'product_variation__name'
        ).annotate(total_count=Count('count'))
        return Response(data)