import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv


load_dotenv()

ELASTIC_HOST = os.getenv('ELASTIC_HOST', 'http://elasticsearch:9200')
ELASTIC_USERNAME = os.getenv('ELASTIC_USERNAME', 'elastic')
ELASTIC_PASSWORD = os.getenv('ELASTIC_PASSWORD', '')

# Create Elasticsearch client with authentication
ELASTIC = Elasticsearch(
    [ELASTIC_HOST],
    basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD) if ELASTIC_PASSWORD else None,
    verify_certs=False,
    ssl_show_warn=False
)

SHOP_INDEX_NAME = 'shops'
PRODUCT_INDEX_NAME = 'products'


def create_indices():
    if not ELASTIC.indices.exists(index=SHOP_INDEX_NAME):
        ELASTIC.indices.create(
            index=SHOP_INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "name": {"type": "text", "analyzer": "standard"}
                    }
                }
            }
        )
    
    if not ELASTIC.indices.exists(index=PRODUCT_INDEX_NAME):
        ELASTIC.indices.create(
            index=PRODUCT_INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "shop_id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "standard"},
                        "about": {"type": "text", "analyzer": "standard"},
                        "on_sale": {"type": "boolean"},
                        "is_active": {"type": "boolean"},
                        "top_sale": {"type": "boolean"},
                        "top_popular": {"type": "boolean"},
                        "sku": {"type": "keyword"},
                        "created_at": {"type": "date"}
                    }
                }
            }
        )