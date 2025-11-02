import os
from dotenv import load_dotenv
import redis


load_dotenv()

redis_client = redis.Redis(
    host=os.getenv('HOST'),  
    port=os.getenv('REDIS_PORT'),
    decode_responses=True  
)