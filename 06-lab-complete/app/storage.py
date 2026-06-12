"""Redis-backed shared storage used by every agent instance."""
import json

import redis

from app.config import settings


redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def check_redis() -> bool:
    return bool(redis_client.ping())


def load_history(user_id: str) -> list[dict]:
    values = redis_client.lrange(f"history:{user_id}", 0, -1)
    return [json.loads(value) for value in values]


def append_history(user_id: str, role: str, content: str) -> None:
    key = f"history:{user_id}"
    pipeline = redis_client.pipeline()
    pipeline.rpush(key, json.dumps({"role": role, "content": content}))
    pipeline.ltrim(key, -settings.max_history_messages, -1)
    pipeline.expire(key, settings.history_ttl_seconds)
    pipeline.execute()
