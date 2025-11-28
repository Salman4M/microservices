import logging

logger = logging.getLogger("cache")
logger.setLevel(logging.INFO)


# ---------------------------------------------------
# PRODUCT KEY BUILDERS
# ---------------------------------------------------

def product_list_key_builder(func, namespace, request, skip=0, limit=100, *args, **kwargs):
    key = f"{namespace}:product:list:skip={skip}:limit={limit}"
    logger.info(f"[CACHE] PRODUCT LIST key built: {key}")
    print(f"[CACHE] PRODUCT LIST key built: {key}")
    return key


def product_detail_key_builder(func, namespace, request, *args, **kwargs):
    product_id = kwargs.get("product_id")
    key = f"{namespace}:product:{product_id}"
    logger.info(f"[CACHE] PRODUCT DETAIL key built: {key}")
    return key


# ---------------------------------------------------
# PRODUCT VARIATION KEY BUILDERS
# ---------------------------------------------------

def variation_list_key_builder(func, namespace, request, *args, **kwargs):
    product_id = kwargs.get("product_id")
    skip = kwargs.get("skip", 0)
    limit = kwargs.get("limit", 100)

    key = f"{namespace}:variation:list:{product_id}:{skip}:{limit}"
    logger.info(
        f"[CACHE] VARIATION LIST key built: {key} "
        f"(product_id={product_id}, skip={skip}, limit={limit})"
    )
    return key


def variation_detail_key_builder(func, namespace, request, *args, **kwargs):
    variation_id = kwargs.get("variation_id")
    key = f"{namespace}:variation:{variation_id}"
    logger.info(f"[CACHE] VARIATION DETAIL key built: {key}")
    return key