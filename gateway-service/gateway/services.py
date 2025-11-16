import os
from dotenv import load_dotenv


load_dotenv()

USER_SERVICE = os.getenv('USER_SERVICE')
SHOP_SERVICE = os.getenv('SHOP_SERVICE')
PRODUCT_SERVICE = os.getenv('PRODUCT_SERVICE')
SHOPCART_SERVICE = os.getenv('SHOPCART_SERVICE')
ORDER_SERVICE = os.getenv('ORDER_SERVICE')
WISHLIST_SERVICE = os.getenv('WISHLIST_SERVICE')
ANALYTIC_SERVICE = os.getenv('ANALYTIC_SERVICE')
ELASTICSEARCH_SERVICE = os.getenv('ELASTICSEARCH_SERVICE')



SERVICE_URLS = {
    'user': USER_SERVICE,
    'shop': SHOP_SERVICE,
    'product': PRODUCT_SERVICE,
    'cart': SHOPCART_SERVICE,
    'order': ORDER_SERVICE,
    'wishlist': WISHLIST_SERVICE,
    'analytic': ANALYTIC_SERVICE,
    'elasticsearch': ELASTICSEARCH_SERVICE

}
