import time

from fastapi import HTTPException, Request

from app.config import get_settings
from app.utils.logger import logger


async def check_rate_limit(request: Request) -> None:
    settings = get_settings()
    redis = getattr(request.app.state, "redis", None)
    if not redis:
        return

    auth = request.headers.get("Authorization", "anonymous")
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW
    limit = settings.RATE_LIMIT_REQUESTS
    key = f"ratelimit:{auth[-16:]}"

    try:
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        count = results[2]

        if count > limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error_code": "RATE_LIMITED",
                    "message": f"Max {limit} requests per {window}s",
                    "retry_after": window,
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Rate limit check error: {e}")
