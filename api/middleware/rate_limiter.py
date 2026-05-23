"""
Redis-based token bucket rate limiter.

Uses a Lua script for atomic token bucket operations
to ensure accurate rate limiting under concurrent load.
"""

from __future__ import annotations

import time

import redis.asyncio as aioredis
from fastapi import Depends, Request

from api.config import Settings, get_settings
from core.exceptions import RateLimitExceededError
from db.models.tenant import Tenant

# Lua script for atomic token bucket rate limiting
# Returns: (allowed: 0|1, remaining_tokens: float, retry_after_seconds: float)
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    -- Initialize bucket
    tokens = max_tokens
    last_refill = now
end

-- Refill tokens based on elapsed time
local elapsed = now - last_refill
local new_tokens = elapsed * refill_rate
tokens = math.min(max_tokens, tokens + new_tokens)

-- Try to consume one token
if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 60)
    return {1, math.floor(tokens), 0}
else
    -- Calculate retry-after
    local deficit = 1 - tokens
    local retry_after = math.ceil(deficit / refill_rate)
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 60)
    return {0, 0, retry_after}
end
"""

# Cached Redis connection
_redis_client: aioredis.Redis | None = None


async def get_redis_client(settings: Settings = Depends(get_settings)) -> aioredis.Redis:
    """Get or create the Redis connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


async def check_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """
    FastAPI dependency that enforces rate limiting.

    Must be used AFTER get_current_tenant (needs tenant in request.state).
    Uses Redis token bucket algorithm for accurate per-tenant limits.

    Raises:
        RateLimitExceededError: If the tenant has exceeded their plan's rate limit.
    """
    tenant: Tenant | None = getattr(request.state, "tenant", None)
    if tenant is None:
        # Skip rate limiting for unauthenticated endpoints
        return

    redis_client = await get_redis_client(settings)

    # Get rate limit for tenant's plan
    max_tokens = settings.get_rate_limit(tenant.plan)
    refill_rate = max_tokens  # Refill = max per second

    # Build unique key per tenant
    bucket_key = f"ratelimit:{tenant.id}"
    now = time.time()

    # Execute atomic Lua script
    result = await redis_client.eval(
        TOKEN_BUCKET_SCRIPT,
        1,
        bucket_key,
        str(max_tokens),
        str(refill_rate),
        str(now),
    )

    allowed, remaining, retry_after = int(result[0]), int(result[1]), int(result[2])

    # Set rate limit headers on response (will be picked up by middleware)
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = max_tokens

    if not allowed:
        raise RateLimitExceededError(retry_after=max(retry_after, 1))
