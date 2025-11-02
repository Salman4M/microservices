from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny  # prod-da öz permission-ların
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import logging

from ..models import * 
from ..serializers import *

from utils.shopcart_client import shopcart_client
from utils.rabbitmq_producer import rabbitmq_producer
import asyncio
import uuid


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
    """
    Create order from user's shopping cart
    
    Steps:
    1. Get cart data from shopcart service via gateway
    2. Validate cart has items
    3. Create order
    4. Create order items from cart items
    5. Publish order.created event to RabbitMQ
    6. ShopCart consumer will clear the cart
    """
    
    # Get user_uuid from authenticated user
    if not hasattr(request.user, 'id'):
        return Response(
            {"error": "Authentication required"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    user_uuid_str = str(request.user.id)
    
    # Validate it's a valid UUID
    try:
        user_uuid = uuid.UUID(user_uuid_str)
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid user UUID: {user_uuid_str}")
        return Response(
            {"error": "Invalid user ID format"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get authorization token from request
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response(
            {"error": "Invalid authorization header"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    auth_token = auth_header.replace('Bearer ', '')
    
    try:
        # 1. Get cart data from shopcart service
        logger.info(f"🛒 Fetching cart for user {user_uuid}")
        cart_data = asyncio.run(shopcart_client.get_user_cart(user_uuid_str, auth_token))
        
        if not cart_data:
            return Response(
                {"error": "Shopping cart not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 2. Validate cart has items
        if not asyncio.run(shopcart_client.validate_cart_items(cart_data)):
            return Response(
                {"error": "Shopping cart is empty or invalid"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_id = cart_data.get('id')
        items = cart_data.get('items', [])
        
        logger.info(f"📦 Creating order from cart {cart_id} with {len(items)} items")
        
        # 3. Create order with UUID
        order = Order.objects.create(
            user_id=user_uuid,  # Now accepts UUID
            is_approved=False
        )
        
        # 4. Create order items from cart items
        created_items = []
        for cart_item in items:
            # Convert product_variation_uuid string to UUID
            try:
                variation_uuid = uuid.UUID(str(cart_item['product_variation_id']))
            except (ValueError, KeyError) as e:
                logger.error(f"Invalid product variation UUID: {e}")
                continue
            
            order_item = OrderItem.objects.create(
                order=order,
                product_variation=variation_uuid,  # Now accepts UUID
                quantity=cart_item['quantity'],
                price=0,  # TODO: Fetch actual price from product service
                status=OrderItem.Status.PROCESSING
            )
            created_items.append(order_item)
        
        if not created_items:
            # If no items were created, delete the order
            order.delete()
            return Response(
                {"error": "Failed to create order items"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"✅ Created order {order.id} with {len(created_items)} items")
        
        # 5. Publish order.created event to RabbitMQ
        try:
            rabbitmq_producer.publish_order_created(
                order_id=order.id,
                user_uuid=user_uuid_str,
                cart_id=cart_id
            )
            logger.info(f"📤 Published order.created event for order {order.id}")
        except Exception as e:
            logger.error(f"⚠️ Failed to publish order.created event: {e}")
            # Don't fail the order creation if event publishing fails
        
        # 6. Return created order
        serializer = OrderSerializer(order)
        return Response(
            {
                "message": "Order created successfully",
                "order": serializer.data
            }, 
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating order: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Failed to create order: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

#KEEP IT HERE
# @api_view(['POST'])
# def create_order_from_shopcart(request):
#     user_id = str(request.user.id)
    
#     shopcart_data = shopcart_client.get_shopcart_data(user_id)
    
#     if not shopcart_data:
#         return Response({"detail": "Shopcart not found"}, status=status.HTTP_404_NOT_FOUND)
    
#     items = shopcart_data.pop('items', [])
    
#     # Order için sadece gerekli field'ları kullan
#     order_data = {"user_id": user_id}
    
#     order_serializer = OrderSerializer(data=order_data)
#     if order_serializer.is_valid():
#         order = order_serializer.save()
#         logger.info(f'Order created successfully - Order ID: {order.id}, User: {user_id}, Items: {len(items)}')
#     else:
#         logger.error(f'Order serializer errors: {order_serializer.errors}')
#         return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     # 2️⃣ OrderItem-ları yarat
#     for item in items:
#         # OrderItem için gerekli field'ları hazırla
#         order_item_data = {
#             'order': order.id,
#             'product_variation': item.get('product_variation_id'),
#             'quantity': item.get('quantity', 1),
#             'status': 1,  # Status.PROCESSING (integer)
#             'price': 0  # Price field required, default to 0 (integer)
#         }
#         item_serializer = OrderItemSerializer(data=order_item_data)
#         if item_serializer.is_valid():
#             item_serializer.save()
#         else:
#             logger.error(f'Order item serializer errors: {item_serializer.errors}')
#             return Response(item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     return Response({"message": "Order and items created successfully"}, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
def update_order_item_status(request, pk):
    try:
        item = OrderItem.objects.get(pk=pk)
    except OrderItem.DoesNotExist:
        return Response({"error": "OrderItem not found"}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get("status")
    if new_status not in dict(OrderItem.Status.choices):
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    item.status = new_status
    item.save()

    item.order.check_and_approve()

    serializer = OrderItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)
