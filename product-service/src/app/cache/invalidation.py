from fastapi.params import Depends
from requests import Session
from fastapi_cache import FastAPICache
from .backend import CACHE_NAMESPACE
from src.app.repositories.v1.product_variation import ProductVariationRepository
from src.app.core.db import get_db

# ------------------------------
# PRODUCT INVALIDATION
# ------------------------------

async def invalidate_product(product_id: str):
    backend = FastAPICache.get_backend()

    # Detail key
    detail_key = f"{CACHE_NAMESPACE}:product:{product_id}"
    await backend.delete(detail_key)

    # Common list variants (skip/limit)
    for skip in (0, 50, 100):
        for limit in (10, 20, 50, 100):
            list_key = f"{CACHE_NAMESPACE}:product:list:skip={skip}:limit={limit}"
            await backend.delete(list_key)


# ------------------------------
# VARIATION INVALIDATION
# ------------------------------

async def invalidate_variation(variation_id: str, db:Session = Depends(get_db)):
    backend = FastAPICache.get_backend()

    repo = ProductVariationRepository(db)
    product_id = repo.get_product_id(variation_id)

    # Detail key
    detail_key = f"{CACHE_NAMESPACE}:variation:{variation_id}"
    await backend.delete(detail_key)

    # List keys tied to its product
    for skip in (0, 50, 100):
        for limit in (10, 20, 50, 100):
            list_key = f"{CACHE_NAMESPACE}:variation:list:product_id={product_id}:skip={skip}:limit={limit}"
            await backend.delete(list_key)

    # Also product might change if variation affects product display but in our case it does not.