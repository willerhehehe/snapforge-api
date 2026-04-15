from fastapi import Header, HTTPException, status

from snapforge.config import settings
from snapforge.db import get_customer_by_api_key, increment_usage


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    if settings.api_key and x_api_key == settings.api_key:
        return x_api_key

    customer = get_customer_by_api_key(x_api_key)
    if not customer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    if not increment_usage(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly quota exceeded ({customer['requests_limit']} requests). Upgrade your plan at /",
        )

    return x_api_key
