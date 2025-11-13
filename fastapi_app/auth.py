import os
import time
from fastapi import Query, HTTPException, status

API_KEY = os.getenv("API_KEY", "supersecretapikey")
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
WINDOW_SECONDS = 3600  # 1 hour

# api_key stays as query param (NOT HEADER)
_request_counters: dict[str, tuple[float, int]] = {}


async def verify_api_key(x_api_key: str = Query(None, alias="x-api-key")):
    """
    Validate API key from query param.
    Swagger shows it exactly as in your screenshot.
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key


async def rate_limiter(x_api_key: str = Query(None, alias="x-api-key")):
    """
    Enforces max RATE_LIMIT requests per API key.
    """

    # Must validate API key first
    await verify_api_key(x_api_key)

    now = time.time()
    window_start, count = _request_counters.get(x_api_key, (now, 0))

    # Reset hourly window
    if now - window_start > WINDOW_SECONDS:
        _request_counters[x_api_key] = (now, 1)
        return x_api_key

    if count >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (100 requests per hour)",
        )

    _request_counters[x_api_key] = (window_start, count + 1)

    return x_api_key
