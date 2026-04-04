import hashlib
import json
from typing import Optional

from app.utils.logger import logger


class Cache:
    def __init__(self, redis_client):
        self.redis = redis_client

    def _make_key(self, data: dict) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return f"vedic:{hashlib.sha256(raw.encode()).hexdigest()}"

    async def get_cached(self, key: str) -> Optional[dict]:
        if not self.redis:
            return None
        try:
            raw = await self.redis.get(key)
            if raw:
                logger.info(f"Cache hit: {key[:20]}...")
                return json.loads(raw)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def set_cached(self, key: str, data: dict, ttl: int = 3600) -> None:
        if not self.redis:
            return
        try:
            await self.redis.set(key, json.dumps(data, default=str), ex=ttl)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
