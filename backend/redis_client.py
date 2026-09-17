import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# decode_responses=True so we get str back instead of bytes everywhere.
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
