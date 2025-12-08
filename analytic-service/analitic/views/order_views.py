from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, FloatField, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import logging
from ..models import Order, OrderItem
from ..services.analitic_service import AnaliticService

logger = logging.getLogger('analitic.views.order_views')

class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for analytics and statistics"""
    
    @action(detail=False, methods=['post'], url_path='order-completed')
    def order_completed(self, request):
        """Order completed endpoint"""
        try:
            data = request.data
            logger.info(f"Received order completed request: order_id={data.get('id')}, items_count={len(data.get('items', []))}")
            logger.info(f"Order items data: {[{'id': i.get('id'), 'product_variation': i.get('product_variation')} for i in data.get('items', [])]}")
            
            service = AnaliticService()
            logger.info(f"Calling AnaliticService.process_order_completed for order_id={data.get('id')}")
            
            # Call service directly - it handles idempotency itself
            order = service.process_order_completed(data)
            
            logger.info(f"Service returned order: order_id={order.order_id}, user_id={order.user_id}")
            
            # Always return 201 if service processed successfully
            return Response({
                'status': 'success',
                'message': 'Order successfully processed',
                'order_id': str(order.order_id),
                'user_id': str(order.user_id),
                'created': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }, status=status.HTTP_201_CREATED)
            
        except KeyError as e:
            logger.error(f"KeyError in order_completed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error', 
                'message': f'Missing field: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Exception in order_completed: {str(e)}", exc_info=True)
            # If error is about order already existing, return 200
            error_message = str(e).lower()
            if 'already exists' in error_message or 'duplicate' in error_message:
                # Try to extract order ID from error message
                order_id_match = re.search(r'order[_\s]?id[_\s]?[:=]?[_\s]?([^\s,]+)', error_message, re.IGNORECASE)
                order_id = order_id_match.group(1) if order_id_match else 'unknown'
                
                return Response({
                    'status': 'success',
                    'message': 'Order already exists',
                    'order_id': order_id
                }, status=status.HTTP_200_OK)
                
            return Response({
                'status': 'error',
                'message': f'Error during processing: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ==================== GET ENDPOINTS ====================
    
    @action(detail=False, methods=['get'], url_path='shops/(?P<shop_id>[^/.]+)/dashboard')
    def shop_dashboard(self, request, shop_id=None):
        """Dashboard statistics for shop"""
        try:
            # Get parameters
            header_shop_id = request.headers.get('X-Shop-ID')
            if not header_shop_id:
                return Response({'status': 'error', 'message': 'X-Shop-ID header missing'}, status=status.HTTP_400_BAD_REQUEST)
            
            if str(shop_id) != str(header_shop_id):
                return Response({'status': 'error', 'message': 'Unauthorized for this shop'}, status=status.HTTP_403_FORBIDDEN)

            days = int(request.GET.get('days', 30))
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Set date range
            if start_date and end_date:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            else:
                end_date = timezone.now()
                start_date = end_date - timedelta(days=days)
            
            # Calculate shop sales data
            shop_orders = OrderItem.objects.filter(
                shop_id=shop_id,
                order__created_at__range=[start_date, end_date]
            )
            
            # General statistics
            total_revenue = shop_orders.aggregate(
                total=Sum(F('price') * F('quantity'))
            )['total'] or 0
            
            total_orders = Order.objects.filter(
                items__shop_id=shop_id,
                created_at__range=[start_date, end_date]
            ).distinct().count()
            
            total_products_sold = shop_orders.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Product distribution by category
            products_by_category = shop_orders.values('product_title').annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum(F('price') * F('quantity'))
            ).order_by('-total_revenue')[:10]
            
            # Daily trends
            from django.db.models.functions import TruncDate
            
            # Daily revenue trends
            daily_revenue_trends = OrderItem.objects.filter(
                shop_id=shop_id,
                order__created_at__range=[start_date, end_date]
            ).annotate(
                date=TruncDate('order__created_at')
            ).values('date').annotate(
                daily_revenue=Sum(F('price') * F('quantity'))
            ).order_by('date')
            
            # Daily order count trends
            daily_orders_trends = Order.objects.filter(
                items__shop_id=shop_id,
                created_at__range=[start_date, end_date]
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                daily_orders=Count('id', distinct=True)
            ).order_by('date')
            
            # Merge daily trends
            daily_trends_map = {}
            
            # Add revenue trends
            for trend in daily_revenue_trends:
                date_str = trend['date'].isoformat()
                if date_str not in daily_trends_map:
                    daily_trends_map[date_str] = {'date': date_str, 'daily_revenue': 0, 'daily_orders': 0}
                daily_trends_map[date_str]['daily_revenue'] = float(trend['daily_revenue'] or 0)
            
            # Add order trends
            for trend in daily_orders_trends:
                date_str = trend['date'].isoformat()
                if date_str not in daily_trends_map:
                    daily_trends_map[date_str] = {'date': date_str, 'daily_revenue': 0, 'daily_orders': 0}
                daily_trends_map[date_str]['daily_orders'] = trend['daily_orders']
            
            daily_trends = list(daily_trends_map.values())
            daily_trends.sort(key=lambda x: x['date'])
            
            result = {
                "shop_id": shop_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "summary": {
                    "total_revenue": float(total_revenue),
                    "total_orders": total_orders,
                    "total_products_sold": total_products_sold,
                    "average_order_value": round(float(average_order_value), 2),
                    "conversion_rate": round((total_orders / max(1, total_products_sold)) * 100, 2) if total_products_sold > 0 else 0
                },
                "top_products": [
                    {
                        "product_name": item['product_title'] or "Unknown Product",
                        "total_sold": item['total_sold'],
                        "total_revenue": float(item['total_revenue'])
                    }
                    for item in products_by_category
                ],
                "daily_trends": daily_trends
            }
            
            return Response(result)
            
        except Exception as e:
            import traceback
            return Response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='shops/(?P<shop_id>[^/.]+)/sales-report')
    def shop_sales_report(self, request, shop_id=None):
        """Detailed sales report for shop"""
        try:
            header_shop_id = request.headers.get('X-Shop-ID')
            if not header_shop_id:
                return Response({'status': 'error', 'message': 'X-Shop-ID header missing'}, status=status.HTTP_400_BAD_REQUEST)
            
            if str(shop_id) != str(header_shop_id):
                return Response({'status': 'error', 'message': 'Unauthorized for this shop'}, status=status.HTTP_403_FORBIDDEN)

            # Get parameters
            time_filter = request.GET.get('time_filter', 'last_30_days')
            product_id = request.GET.get('product_id')
            sort_by = request.GET.get('sort_by', 'order_date')
            order_dir = request.GET.get('order', 'desc')
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 50))
            
            # Time filter
            end_date = timezone.now()
            if time_filter == 'today':
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_filter == 'yesterday':
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                end_date = start_date + timedelta(days=1)
            elif time_filter == 'last_7_days':
                start_date = end_date - timedelta(days=7)
            elif time_filter == 'last_30_days':
                start_date = end_date - timedelta(days=30)
            elif time_filter == 'last_90_days':
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Base queryset
            order_items = OrderItem.objects.filter(
                shop_id=shop_id,
                order__created_at__range=[start_date, end_date]
            ).select_related('order')
            
            # Additional filters
            if product_id:
                order_items = order_items.filter(product_id=product_id)
            
            # Sorting
            if sort_by == 'order_date':
                order_by = '-order__created_at' if order_dir == 'desc' else 'order__created_at'
            elif sort_by == 'price':
                order_by = '-price' if order_dir == 'desc' else 'price'
            elif sort_by == 'quantity':
                order_by = '-quantity' if order_dir == 'desc' else 'quantity'
            elif sort_by == 'profit':
                order_items = order_items.annotate(
                    profit=ExpressionWrapper(F('price') - F('base_price'), output_field=FloatField())
                )
                order_by = '-profit' if order_dir == 'desc' else 'profit'
            else:
                order_by = '-order__created_at'
            
            order_items = order_items.order_by(order_by)
            
            # Pagination
            total_count = order_items.count()
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_items = order_items[start_index:end_index]
            
            # Prepare result
            result = []
            for item in paginated_items:
                profit = float(item.price) - float(item.base_price)
                total_price = float(item.price) * item.quantity
                
                result.append({
                    'order_id': str(item.order.order_id),
                    'order_date': item.order.created_at.isoformat(),
                    'user_id': str(item.order.user_id),
                    'product_id': str(item.product_id) if item.product_id else None,
                    'product_title': item.product_title,
                    'product_sku': item.product_sku,
                    'quantity': item.quantity,
                    'base_price': float(item.base_price),
                    'selling_price': float(item.price),
                    'total_price': round(total_price, 2),
                    'profit_per_item': round(profit, 2),
                    'total_profit': round(profit * item.quantity, 2),
                    'size': item.size,
                    'color': item.color
                })
            
            # General statistics
            total_stats = order_items.aggregate(
                total_revenue=Sum(F('price') * F('quantity')),
                total_products=Sum('quantity'),
                total_orders=Count('order_id', distinct=True),
                total_profit=Sum(ExpressionWrapper(
                    (F('price') - F('base_price')) * F('quantity'), 
                    output_field=FloatField()
                ))
            )
            
            response_data = {
                "shop_id": shop_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "time_filter": time_filter
                },
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size
                },
                "summary": {
                    "total_revenue": float(total_stats['total_revenue'] or 0),
                    "total_products_sold": total_stats['total_products'] or 0,
                    "total_orders": total_stats['total_orders'] or 0,
                    "total_profit": float(total_stats['total_profit'] or 0),
                    "average_order_value": round(float(total_stats['total_revenue'] or 0) / max(1, total_stats['total_orders'] or 0), 2)
                },
                "sales": result
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='shops/(?P<shop_id>[^/.]+)/products-performance')
    def shop_products_performance(self, request, shop_id=None):
        """Mağaza məhsul performansı"""
        try:
            header_shop_id = request.headers.get('X-Shop-ID')
            if not header_shop_id:
                return Response({'status': 'error', 'message': 'X-Shop-ID header missing'}, status=status.HTTP_400_BAD_REQUEST)
            
            if str(shop_id) != str(header_shop_id):
                return Response({'status': 'error', 'message': 'Unauthorized for this shop'}, status=status.HTTP_403_FORBIDDEN)

            days = int(request.GET.get('days', 30))
            limit = int(request.GET.get('limit', 20))
            
            start_date = timezone.now() - timedelta(days=days)
            
            products_stats = OrderItem.objects.filter(
                shop_id=shop_id,
                order__created_at__gte=start_date
            ).values(
                'product_id', 'product_title', 'product_sku'
            ).annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum(F('price') * F('quantity')),
                total_profit=Sum(ExpressionWrapper(
                    (F('price') - F('base_price')) * F('quantity'), 
                    output_field=FloatField()
                )),
                average_price=Avg('price'),
                order_count=Count('order_id', distinct=True)
            ).order_by('-total_revenue')[:limit]
            
            result = []
            for product in products_stats:
                result.append({
                    "product_id": str(product['product_id']) if product['product_id'] else "N/A",
                    "product_title": product['product_title'],
                    "product_sku": product['product_sku'],
                    "total_sold": product['total_sold'] or 0,
                    "total_revenue": float(product['total_revenue'] or 0),
                    "total_profit": float(product['total_profit'] or 0),
                    "average_price": float(product['average_price'] or 0),
                    "order_count": product['order_count'],
                    "profit_margin": round((float(product['total_profit'] or 0) / float(product['total_revenue'] or 1)) * 100, 2)
                })
            
            return Response({
                "shop_id": shop_id,
                "period_days": days,
                "products_count": len(result),
                "products": result
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# FUNCTION-BASED VIEW
@csrf_exempt
def analitic_order_completed(request):
    """Function-based view for order completed"""
    if request.method == 'POST':
        try:
            # Read JSON data
            data = json.loads(request.body)
            service = AnaliticService()
            
            # Call service directly - it handles idempotency itself
            order = service.process_order_completed(data)
            
            # Always return 201 if service processed successfully
            return JsonResponse({
                'status': 'success',
                'message': 'Order successfully processed',
                'order_id': str(order.order_id),
                'user_id': str(order.user_id),
                'created': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format'
            }, status=400)
            
        except KeyError as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Missing field: {str(e)}'
            }, status=400)
            
        except Exception as e:
            # If error is about order already existing, return 200
            error_message = str(e).lower()
            if 'already exists' in error_message or 'duplicate' in error_message:
                # Try to extract order ID from error message
                order_id_match = re.search(r'order[_\s]?id[_\s]?[:=]?[_\s]?([^\s,]+)', error_message, re.IGNORECASE)
                order_id = order_id_match.group(1) if order_id_match else 'unknown'
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Order already exists',
                    'order_id': order_id
                }, status=200)
                
            return JsonResponse({
                'status': 'error',
                'message': f'Error during processing: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST method allowed'
    }, status=405)