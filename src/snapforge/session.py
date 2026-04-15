from __future__ import annotations

import hashlib
import hmac
import json
import time

from fastapi import Request, Response

from snapforge.config import settings

COOKIE_NAME = "sf_session"
MAX_AGE = 30 * 24 * 3600  # 30 days


def _sign(data: str) -> str:
    sig = hmac.new(settings.session_secret.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{data}.{sig}"


def _verify(token: str) -> str | None:
    if "." not in token:
        return None
    data, sig = token.rsplit(".", 1)
    expected = hmac.new(settings.session_secret.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmac.compare_digest(sig, expected):
        return None
    return data


def create_session(response: Response, api_key: str, role: str = "user"):
    payload = json.dumps({"key": api_key, "role": role, "exp": int(time.time()) + MAX_AGE})
    is_prod = bool(settings.base_url)
    response.set_cookie(
        COOKIE_NAME, _sign(payload), max_age=MAX_AGE,
        httponly=True, samesite="lax", secure=is_prod,
    )


def get_session(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    data = _verify(token)
    if not data:
        return None
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, ValueError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload


def clear_session(response: Response):
    response.delete_cookie(COOKIE_NAME)
