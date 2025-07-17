from typing import Optional
from redis.asyncio import Redis

redis: Optional[Redis] = None


async def init_redis(uri: str) -> None:
    global redis
    redis = Redis.from_url(uri, decode_responses=True)

    try:
        await redis.ping()
    except Exception as exc:
        raise RuntimeError(
            f'Failed to connect to Redis at {uri}: {exc}'
        )
