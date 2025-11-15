from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny  
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import logging
from utils.rabbitmq_producer import rabbitmq_producer
from utils.shopcart_client import shopcart_client
from utils.product_client import product_client
from utils.shop_client import shop_client
from ..models import * 
from ..serializers import *

logger = logging.getLogger(__name__)



#Order Create
@api_view(['GET', 'POST'])
def orders_list_create(request):
    if request.method == 'GET':
        orders = Order.objects.all().order_by('-id')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['GET', 'PATCH', 'DELETE'])
def orders_detail(request, pk):
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



#OrderItem
# GET / POST
@api_view(['GET', 'POST'])
def orderitems_list_create(request):
    if request.method == 'GET':
        items = OrderItem.objects.select_related('order').all().order_by('-id')
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = OrderItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET / PATCH / DELETE /order-items/<id>/
@api_view(['GET', 'PATCH', 'DELETE'])
def orderitems_detail(request, pk):
    try:
        item = OrderItem.objects.get(pk=pk)
    except OrderItem.DoesNotExist:
        return Response({"error": "OrderItem not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = OrderItemSerializer(item)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = OrderItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['POST'])
def create_order_from_shopcart(request):
    user_id = str(request.user.id)

    shopcart_data = shopcart_client.get_shopcart_data(user_id)

    if not shopcart_data:
        return Response({"detail": "Shopcart not found"}, status=status.HTTP_404_NOT_FOUND)
    
    cart_id = shopcart_data.get('id')
    items = shopcart_data.pop('items', [])

    if not items:
        return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f'Creating order from shopcart - User: {user_id}, Cart ID: {cart_id}, Items: {len(items)}')
    order_data = {"user_id": user_id}
    logger.info("This is your items {items}")
    order_serializer = OrderSerializer(data=order_data)
    if order_serializer.is_valid():
        order = order_serializer.save()
        logger.info(f'Order created successfully - Order ID: {order.id}, User: {user_id}, Items: {len(items)}')
    else:
        logger.error(f'Order serializer errors: {order_serializer.errors}')
        return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    event_items = []
    for item in items:
        ####################################################################################last changes
        variation_id = item.get('product_variation_id')
        if not variation_id:
            logger.error(f'Missing product_variation_id in cart item')
            return Response({"error": "Missing product_variation_id"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch product_id and shop_id from product service
        variation_data = product_client.get_variation(str(variation_id), user_id=user_id)
        if not variation_data:
            logger.error(f'Product variation not found: {variation_id}')
            return Response({"error": f"Product variation not found: {variation_id}"}, status=status.HTTP_404_NOT_FOUND)
        
        product_id = str(variation_data.get("product_id")) if variation_data.get("product_id") else None
        if not product_id:
            logger.error(f'Product ID not found in variation data: {variation_id}')
            return Response({"error": "Product ID not found in variation"}, status=status.HTTP_404_NOT_FOUND)
        
        product_data = product_client.get_product(product_id, user_id=user_id)
        if not product_data:
            logger.error(f'Product not found: {product_id}')
            return Response({"error": f"Product not found: {product_id}"}, status=status.HTTP_404_NOT_FOUND)
        
        shop_id = str(product_data.get("shop_id")) if product_data.get("shop_id") else None
        if not shop_id:
            logger.error(f'Shop ID not found in product data: {product_id}')
            return Response({"error": "Shop ID not found in product"}, status=status.HTTP_404_NOT_FOUND)
    
        order_item_data = {
            'order': order.id,
            'product_variation': variation_id,
            'product_id': product_id,
            'shop_id': shop_id,
            'quantity': item.get('quantity', 1),
            'status': 1,  
            'price': 0  
        }
        ####################################################################################last changes

        item_serializer = OrderItemSerializer(data=order_item_data)
        if item_serializer.is_valid():
            item_serializer.save()
        else:
            logger.error(f'Order item serializer errors: {item_serializer.errors}')
            return Response(item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        event_items.append({
            'product_variation_id': str(item.get('product_variation_id')),
            'quantity': item.get('quantity', 1)
        })

    try:
        success = rabbitmq_producer.publish_order_created(
            order_id=order.id,
            user_uuid=user_id,
            cart_id=cart_id,
            items=event_items  
        )
        
        if success:
            logger.info(f'✅ Published order.created event - Order: {order.id}, Cart: {cart_id}, Items: {len(event_items)}')
        else:
            logger.warning(f'⚠️ Failed to publish order.created event - Order: {order.id}')
    except Exception as e:
        logger.error(f'❌ Error publishing order.created event: {e}')
        # Don't fail the order creation if event publishing fails

    return Response(
        {
            "message": "Order created successfully",
            "order_id": order.id,
            "items_count": len(items)
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['PATCH'])
def update_order_item_status(request, pk):
    try:
        item = OrderItem.objects.get(pk=pk)
    except OrderItem.DoesNotExist:
        logger.warning(f'OrderItem {pk} not found')
        return Response({"error": "OrderItem not found"}, status=status.HTTP_404_NOT_FOUND)
    
    new_status = request.data.get("status")
    if new_status not in dict(OrderItem.Status.choices):
        logger.warning(f'Invalid status {new_status} for OrderItem {pk}')
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    # Use stored shop_id and product_id instead of making network calls
    shop_id = item.shop_id
    product_id = item.product_id
    
    # Fallback to network calls only if data is missing (shouldn't happen if created from shopcart)
    if not shop_id or not product_id:
        logger.warning(f'Missing shop_id or product_id for OrderItem {item.id}, fetching from product service')
        variation_id = str(item.product_variation)
        variation_data = product_client.get_variation(variation_id, user_id=user_id)
        if variation_data and not product_id:
            product_id = str(variation_data.get("product_id")) if variation_data.get("product_id") else None
        
        if product_id and not shop_id:
            product_data = product_client.get_product(product_id, user_id=user_id)
            if product_data:
                shop_id = str(product_data.get("shop_id")) if product_data.get("shop_id") else None
    
    if not shop_id:
        return Response({"error": "Shop ID not found for this order item"}, status=status.HTTP_404_NOT_FOUND)
    
    user_id = str(request.user.id)
    user_shop_ids = shop_client.get_user_shop_ids(user_id)

    if shop_id not in user_shop_ids:
        return Response({"error": "Forbidden: You do not own this shop's item"}, status=status.HTTP_403_FORBIDDEN)

    old_status = item.status
    item.status = new_status
    if product_id and not item.product_id:
        item.product_id = product_id
    if shop_id and not item.shop_id:
        item.shop_id = shop_id
    item.save()

    item.order.check_and_approve()

    # Publish status update event for other services (notification, analytics, etc.)
    # Note: Shop-service doesn't need this event as it updates via API response
    try:
        success = rabbitmq_producer.publish_order_item_status_updated(
            order_item_id=item.id,
            order_id=item.order.id,
            shop_id=str(shop_id),
            status=new_status
        )
        if success:
            logger.debug(f'Published order.item.status.updated event - OrderItem: {item.id}, Status: {new_status}')
        else:
            logger.warning(f'Failed to publish order.item.status.updated event - OrderItem: {item.id}')
    except Exception as e:
        logger.error(f'Error publishing order.item.status.updated event: {e}', exc_info=True)

    serializer = OrderItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)