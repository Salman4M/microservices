from fastapi import FastAPI, Query, APIRouter
from .documents import create_indices, SHOP_INDEX_NAME, PRODUCT_INDEX_NAME, ELASTIC
from .logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix='/api/elasticsearch', tags=['ElasticSearch'])
app = FastAPI(title="Elasticsearch Service API", version="1.0.0")


@router.get('/search/')
def search_all(
    query: str = Query(..., description='Search query for shops and products'),
    size: int = Query(10, description='Number of results per type')
):
    """
    Unified search endpoint that searches across shops and products
    """
    results = {
        'shops': [],
        'products': []
    }
    
    # Search shops
    try:
        shop_result = ELASTIC.search(
            index=SHOP_INDEX_NAME,
            query={
                'match': {
                    'name': {
                        'query': query,
                        'fuzziness': 'AUTO'  
                    }
                }
            },
            size=size
        )
        results['shops'] = [hit['_source'] for hit in shop_result['hits']['hits']]
    except Exception as e:
        logger.error(f"Error searching shops: {e}", exc_info=True)
    
    # Search products
    try:
        product_result = ELASTIC.search(
            index=PRODUCT_INDEX_NAME,
            query={
                'multi_match': {
                    'query': query,
                    'fields': ['title^2', 'about'],
                    'fuzziness': 'AUTO'
                }
            },
            size=size
        )
        results['products'] = [hit['_source'] for hit in product_result['hits']['hits']]
    except Exception as e:
        logger.error(f"Error searching products: {e}", exc_info=True)
    
    return results


@router.get('/shop/{shop_id}/products/')
def get_products_by_shop(
    shop_id: str,
    size: int = Query(100, description='Number of results to return')
):
    """
    Get all products for a specific shop by shop_id
    Returns only products
    """
    if not shop_id or shop_id.strip() == '':
        return {
            'products': [],
            'total': 0,
            'error': 'shop_id is required'
        }
    
    # Normalize shop_id - remove any whitespace
    shop_id = shop_id.strip()
    
    try:
        if not ELASTIC.indices.exists(index=PRODUCT_INDEX_NAME):
            logger.error(f"Index '{PRODUCT_INDEX_NAME}' does not exist")
            return {
                'products': [],
                'total': 0,
                'error': 'Products index does not exist. Please create a product first.'
            }
        
        # Try term query first (exact match for keyword field)
        result = ELASTIC.search(
            index=PRODUCT_INDEX_NAME,
            query={
                'term': {
                    'shop_id': shop_id
                }
            },
            size=size
        )
        
        total = result['hits']['total']['value']
        
        if total > 0:
            products = [hit['_source'] for hit in result['hits']['hits']]
            return {
                'products': products,
                'total': total
            }
        
        # If term query didn't work, try match query (more flexible)
        result = ELASTIC.search(
            index=PRODUCT_INDEX_NAME,
            query={
                'match': {
                    'shop_id': shop_id
                }
            },
            size=size
        )
        
        total = result['hits']['total']['value']
        
        if total > 0:
            products = [hit['_source'] for hit in result['hits']['hits']]
            return {
                'products': products,
                'total': total
            }
        
        return {
            'products': [],
            'total': 0,
            'error': f'No products found for shop_id={shop_id}'
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error searching products by shop_id='{shop_id}': {error_msg}", exc_info=True)
        
        # Check if it's index not found error
        if 'index_not_found_exception' in error_msg.lower() or 'no such index' in error_msg.lower():
            return {
                'products': [],
                'total': 0,
                'error': 'Products index does not exist. Please create a product first.',
                'details': error_msg
            }
        
        return {
            'products': [],
            'total': 0,
            'error': error_msg
        }


app.include_router(router)


@app.on_event('startup')
def startup_event():
    try:
        create_indices()
    except Exception as e:
        logger.error(f"Could not create indices: {e}", exc_info=True)