"""Distributed sliding-window rate limiting backed by Redis."""
import time
import uuid

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.config import settings
from app.storage import redis_client


_SLIDING_WINDOW = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
local count = redis.call('ZCARD', KEYS[1])
if count >= tonumber(ARGV[3]) then
    return 0
end
redis.call('ZADD', KEYS[1], ARGV[2], ARGV[4])
redis.call('EXPIRE', KEYS[1], 60)
return 1
"""


def check_rate_limit(user_id: str) -> None:
    now_ms = int(time.time() * 1000)
    key = f"rate:{user_id}"
    try:
        allowed = redis_client.eval(
            _SLIDING_WINDOW,
            1,
            key,
            now_ms - 60_000,
            now_ms,
            settings.rate_limit_per_minute,
            f"{now_ms}:{uuid.uuid4().hex}",
        )
    except RedisError as exc:
        raise HTTPException(503, "Rate limiter unavailable") from exc

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
