# backend/redis_client.py

import os
import redis.asyncio as redis
from kombu.utils.url import safequote
from logger import logger

# Get and encode host safely
redis_host = safequote(os.environ.get('REDIS_HOST', 'localhost'))
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_db = int(os.environ.get('REDIS_DB', 0))

# Create Redis client
redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

# Add value to Redis with optional expiration
async def add_key_value_redis(key, value, expire=None):
    try:
        await redis_client.set(key, value)
        if expire:
            await redis_client.expire(key, expire)
        logger.debug(f"[Redis] SET {key} (expire={expire})")
    except Exception as e:
        logger.exception(f"[Redis] Failed to SET key '{key}'")

# Get value from Redis
async def get_value_redis(key):
    try:
        value = await redis_client.get(key)
        logger.debug(f"[Redis] GET {key} -> {'HIT' if value else 'MISS'}")
        return value
    except Exception as e:
        logger.exception(f"[Redis] Failed to GET key '{key}'")
        return None

# Delete a key from Redis
async def delete_key_redis(key):
    try:
        await redis_client.delete(key)
        logger.debug(f"[Redis] DEL {key}")
    except Exception as e:
        logger.exception(f"[Redis] Failed to DEL key '{key}'")
