from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from ..models import ProductView, Product
from ..serializers import ProductViewSerializer, ProductViewInputSerializer

class ProductViewViewSet(viewsets.ModelViewSet):
    """Məhsul baxışlarını idarə edən ViewSet"""
    queryset = ProductView.objects.all()
    serializer_class = ProductViewSerializer
    http_method_names = ['get', 'post']
    
    def create(self, request):
        """
        POST /api/v1/analitic-product-view/ - YENİ FORMAT  
        Göndərilən data: {"product_uuid": "...", "product_name": "..."}
        """
        input_serializer = ProductViewInputSerializer(data=request.data)
        if input_serializer.is_valid():
            data = input_serializer.validated_data
            product_uuid = data['product_uuid']
            product_name = data['product_name']
            
            try:
                # Məhsulu yarat və ya yenilə
                product, created = Product.objects.get_or_create(
                    external_id=product_uuid,
                    defaults={
                        'name': product_name,
                        'external_id': product_uuid
                    }
                )
                
                # Əgər məhsul artıq varsa və adı dəyişibsə, yenilə
                if not created and product.name != product_name:
                    product.name = product_name
                    product.save()
                
                # Baxış qeydini yarat
                product_view = ProductView.objects.create(
                    product=product,
                    viewed_at=timezone.now()
                )
                
                # Serializer ilə cavab qaytar
                response_serializer = ProductViewSerializer(product_view)
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
        """Məhsul baxış statistikası - YENİ FORMAT"""
        product_id = request.GET.get('product_id')
        
        # Əgər product_id verilibsə, tək məhsulun statistikasını göstər
        if product_id:
            return self._get_single_product_stats(product_id)
        else:
            # Əgər product_id YOXDURSA, bütün məhsulların statistikasını göstər
            return self._get_all_products_stats()
    
    def _get_single_product_stats(self, product_id):
        """Tək məhsulun statistikası"""
        try:
            product = Product.objects.get(external_id=product_id)
            product_name = product.name
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # BÜTÜN məhsulların ümumi baxış sayı
        total_all_products_views = ProductView.objects.count()
        
        # Bu məhsulun baxışları üçün base queryset
        product_views_queryset = ProductView.objects.filter(product__external_id=product_id)
        
        # Bu məhsulun ümumi baxış sayı
        product_total_views = product_views_queryset.count()
        
        # Faizi hesabla (bütün baxışlar içində bu məhsulun payı)
        if total_all_products_views > 0:
            percentage = (product_total_views / total_all_products_views) * 100
        else:
            percentage = 0
        
        # Müxtəlif periodlar üçün statistikaları hesabla
        periods = [7, 30, 90]
        period_views = {}
        
        for days in periods:
            start_date = timezone.now() - timedelta(days=days)
            period_views[days] = product_views_queryset.filter(viewed_at__gte=start_date).count()
        
        result = {
            "product_name": product_name,
            "product_id": product_id,
            "total_views": product_total_views,
            "total_views_7days": period_views[7],
            "total_views_30days": period_views[30],
            "total_views_90days": period_views[90],
            "percentage_of_all_views": round(percentage, 2),
            "total_views_all_products": total_all_products_views
        }
        
        return Response(result)
    
    def _get_all_products_stats(self):
        """BÜTÜN məhsulların ümumi statistikası"""
        # Bütün məhsulların ümumi baxış sayı
        total_all_products_views = ProductView.objects.count()
        
        # Bütün məhsulların baxış statistikası
        all_products_stats = ProductView.objects.values(
            'product__name', 
            'product__external_id'
        ).annotate(
            total_views=Count('id'),
            total_views_7days=Count('id', filter=Q(viewed_at__gte=timezone.now()-timedelta(days=7))),
            total_views_30days=Count('id', filter=Q(viewed_at__gte=timezone.now()-timedelta(days=30))),
            total_views_90days=Count('id', filter=Q(viewed_at__gte=timezone.now()-timedelta(days=90)))
        ).order_by('-total_views')
        
        # Faizləri hesabla
        formatted_stats = []
        for product in all_products_stats:
            if total_all_products_views > 0:
                percentage = round((product['total_views'] / total_all_products_views) * 100, 2)
            else:
                percentage = 0
            
            formatted_stats.append({
                "product_name": product['product__name'],
                "product_id": product['product__external_id'],
                "total_views": product['total_views'],
                "total_views_7days": product['total_views_7days'],
                "total_views_30days": product['total_views_30days'],
                "total_views_90days": product['total_views_90days'],
                "percentage_of_all_views": percentage
            })
        
        result = {
            "total_views_all_products": total_all_products_views,
            "products": formatted_stats,
            "total_products": len(formatted_stats)
        }
        
        return Response(result)

    @action(detail=False, methods=['get'], url_path='simple-stats')
    def simple_stats(self, request):
        """SADƏ formada məhsul baxış statistikası (köhnə format)"""
        days = request.GET.get('days', 30)
        product_id = request.GET.get('product_id')
        
        start_date = timezone.now() - timedelta(days=int(days))
        
        queryset = ProductView.objects.filter(viewed_at__gte=start_date)
        if product_id:
            queryset = queryset.filter(product__external_id=product_id)
        
        # DÜZƏLİŞ: product__external_id ilə
        stats = queryset.values('product__name', 'product__external_id').annotate(
            total_views=Count('id'),
            daily_avg=Count('id') / int(days)
        ).order_by('-total_views')
        
        # Formatı düzəlt
        formatted_stats = []
        for item in stats:
            formatted_stats.append({
                'product_name': item['product__name'],
                'product_id': item['product__external_id'],
                'total_views': item['total_views'],
                'daily_avg': round(item['daily_avg'], 2)
            })
        
        return Response(formatted_stats)