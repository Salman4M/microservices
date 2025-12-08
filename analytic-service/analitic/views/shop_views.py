from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from ..models import ShopView, Shop
from ..serializers import ShopViewSerializer, ShopViewInputSerializer

class ShopViewViewSet(viewsets.ModelViewSet):
    """Mağaza baxışlarını idarə edən ViewSet"""
    queryset = ShopView.objects.all()
    serializer_class = ShopViewSerializer
    http_method_names = ['get', 'post']
    
    def create(self, request):
        """
        POST /api/v1/analitic-shop-view/ - YENİ FORMAT
        Göndərilən data: {"shop_uuid": "...", "shop_name": "..."}
        """
        input_serializer = ShopViewInputSerializer(data=request.data)
        if input_serializer.is_valid():
            data = input_serializer.validated_data
            shop_uuid = data['shop_uuid']
            shop_name = data['shop_name']
            
            try:
                # Mağazanı yarat və ya yenilə
                shop, created = Shop.objects.get_or_create(
                    external_id=shop_uuid,
                    defaults={
                        'name': shop_name,
                        'external_id': shop_uuid
                    }
                )
                
                # Əgər mağaza artıq varsa və adı dəyişibsə, yenilə
                if not created and shop.name != shop_name:
                    shop.name = shop_name
                    shop.save()
                
                # Baxış qeydini yarat
                shop_view = ShopView.objects.create(
                    shop=shop,
                    viewed_at=timezone.now()
                )
                
                # Serializer ilə cavab qaytar
                response_serializer = ShopViewSerializer(shop_view)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {
                        'status': 'error',
                        'message': f'Internal server error: {str(e)}'
                    }, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Mağaza baxış statistikası - YENİ FORMAT"""
        shop_id = request.GET.get('shop_id')
        
        # Əgər shop_id verilibsə, tək mağazanın statistikasını göstər
        if shop_id:
            return self._get_single_shop_stats(shop_id)
        else:
            # Əgər shop_id YOXDURSA, bütün mağazaların statistikasını göstər
            return self._get_all_shops_stats()
    
    def _get_single_shop_stats(self, shop_id):
        """Tək mağazanın statistikası"""
        try:
            shop = Shop.objects.get(external_id=shop_id)
            shop_name = shop.name
        except Shop.DoesNotExist:
            return Response(
                {"error": "Shop not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # BÜTÜN mağazaların ümumi baxış sayı
        total_all_shops_views = ShopView.objects.count()
        
        # Bu mağazanın baxışları üçün base queryset
        shop_views_queryset = ShopView.objects.filter(shop__external_id=shop_id)
        
        # Bu mağazanın ümumi baxış sayı
        shop_total_views = shop_views_queryset.count()
        
        # Faizi hesabla (bütün baxışlar içində bu mağazanın payı)
        if total_all_shops_views > 0:
            percentage = (shop_total_views / total_all_shops_views) * 100
        else:
            percentage = 0
        
        # Müxtəlif periodlar üçün statistikaları hesabla
        periods = [7, 30, 90]
        period_views = {}
        
        for days in periods:
            start_date = timezone.now() - timedelta(days=days)
            period_views[days] = shop_views_queryset.filter(viewed_at__gte=start_date).count()
        
        result = {
            "shop_name": shop_name,
            "shop_id": shop_id,
            "total_views": shop_total_views,
            "total_views_7days": period_views[7],
            "total_views_30days": period_views[30],
            "total_views_90days": period_views[90],
            "percentage_of_all_views": round(percentage, 2),
            "total_views_all_shops": total_all_shops_views
        }
        
        return Response(result)
    
    def _get_all_shops_stats(self):
        """BÜTÜN mağazaların ümumi statistikası"""
        # Bütün mağazaların ümumi baxış sayı
        total_all_shops_views = ShopView.objects.count()
        
        # Bütün mağazaların baxış statistikası
        all_shops_stats = ShopView.objects.values(
            'shop__name', 
            'shop__external_id'
        ).annotate(
            total_views=Count('id'),
            total_views_7days=Count('id', filter=Q(viewed_at__gte=timezone.now()-timedelta(days=7))),
            total_views_30days=Count('id', filter=Q(viewed_at__gte=timezone.now()-timedelta(days=30))),
            total_views_90days=Count('id', filter=Q(viewed_at__gte=timezone.now()-timedelta(days=90)))
        ).order_by('-total_views')
        
        # Faizləri hesabla
        formatted_stats = []
        for shop in all_shops_stats:
            if total_all_shops_views > 0:
                percentage = round((shop['total_views'] / total_all_shops_views) * 100, 2)
            else:
                percentage = 0
            
            formatted_stats.append({
                "shop_name": shop['shop__name'],
                "shop_id": shop['shop__external_id'],
                "total_views": shop['total_views'],
                "total_views_7days": shop['total_views_7days'],
                "total_views_30days": shop['total_views_30days'],
                "total_views_90days": shop['total_views_90days'],
                "percentage_of_all_views": percentage
            })
        
        result = {
            "total_views_all_shops": total_all_shops_views,
            "shops": formatted_stats,
            "total_shops": len(formatted_stats)
        }
        
        return Response(result)

    @action(detail=False, methods=['get'], url_path='simple-stats')
    def simple_stats(self, request):
        """SADƏ formada mağaza baxış statistikası (köhnə format)"""
        days = request.GET.get('days', 30)
        shop_id = request.GET.get('shop_id')
        
        start_date = timezone.now() - timedelta(days=int(days))
        
        queryset = ShopView.objects.filter(viewed_at__gte=start_date)
        if shop_id:
            queryset = queryset.filter(shop__external_id=shop_id)
        
        # Mağaza statistikası
        stats = queryset.values('shop__name', 'shop__external_id').annotate(
            total_views=Count('id'),
            daily_avg=Count('id') / int(days)
        ).order_by('-total_views')
        
        # Formatı düzəlt
        formatted_stats = []
        for item in stats:
            formatted_stats.append({
                'shop_name': item['shop__name'],
                'shop_id': item['shop__external_id'],
                'total_views': item['total_views'],
                'daily_avg': round(item['daily_avg'], 2)
            })
        
        return Response(formatted_stats)