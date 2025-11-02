from django.urls import path
from .views import *

urlpatterns = [
    path('orders/', views_v1.orders_list_create, name='orders_list_create'),
    path('order-items/', views_v1.orderitems_list_create, name='orderitems_list_create'),

    path('orders/<int:pk>/', views_v1.orders_detail, name='orders_detail'),
    path('order-items/<int:pk>/', views_v1.orderitems_detail, name='orderitems_detail'),

    path('orders-from-shopcart/', views_v1.create_order_from_shopcart, name='orders_from_shopcart'),

    path('order-items/<int:pk>/status/', views_v1.update_order_item_status, name='update-orderitem-status'),
    
]
