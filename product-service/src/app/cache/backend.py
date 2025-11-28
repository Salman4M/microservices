from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# Optionally Redis:
# from fastapi_cache.backends.redis import RedisBackend
# import redis.asyncio as redis

CACHE_NAMESPACE = "product-cache"

async def init_cache(app):
    """
    Initialize cache system with in-memory backend.
    """
    backend = InMemoryBackend()

    # If using Redis later:
    # redis_client = redis.Redis(host="redis", port=6379, db=0)
    # backend = RedisBackend(redis_client)

    FastAPICache.init(backend, prefix=CACHE_NAMESPACE)