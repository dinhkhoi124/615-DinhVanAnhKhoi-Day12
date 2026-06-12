"""Distributed monthly budget guard backed by Redis."""
from datetime import datetime, timezone

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.config import settings
from app.storage import redis_client


_RECORD_COST = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local amount = tonumber(ARGV[1])
local budget = tonumber(ARGV[2])
if current + amount > budget then
    return -1
end
local total = redis.call('INCRBYFLOAT', KEYS[1], amount)
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]))
return total
"""


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006


def check_and_record_cost(user_id: str, input_tokens: int, output_tokens: int) -> float:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    key = f"cost:{user_id}:{month}"
    amount = estimate_cost(input_tokens, output_tokens)
    try:
        total = redis_client.eval(
            _RECORD_COST,
            1,
            key,
            amount,
            settings.monthly_budget_usd,
            32 * 24 * 60 * 60,
        )
    except RedisError as exc:
        raise HTTPException(503, "Budget service unavailable") from exc

    if float(total) < 0:
        raise HTTPException(402, "Monthly budget exhausted")
    return float(total)