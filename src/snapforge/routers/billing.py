from __future__ import annotations

import hashlib
import hmac
import json

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse

from snapforge.config import settings
from snapforge.db import (
    create_customer, get_customer_by_email,
    get_customer_by_stripe_id, upgrade_customer, create_subscription,
)

router = APIRouter()

PADDLE_PRICE_IDS = {}
PADDLE_TIER_FROM_PRICE = {}


def _init_paddle_prices():
    global PADDLE_PRICE_IDS, PADDLE_TIER_FROM_PRICE
    PADDLE_PRICE_IDS = {
        "pro": settings.paddle_price_pro,
        "business": settings.paddle_price_business,
    }
    PADDLE_TIER_FROM_PRICE = {v: k for k, v in PADDLE_PRICE_IDS.items() if v}


@router.get("/billing/free-key")
async def free_key(email: str = Query(...)):
    existing = get_customer_by_email(email)
    if existing:
        return {"message": "Account already exists. Use Forgot API Key to recover it, or contact the administrator."}
    customer = create_customer(email, tier="free")
    return {"api_key": customer["api_key"], "tier": "free", "requests_limit": 100}


@router.get("/billing/config")
async def billing_config():
    _init_paddle_prices()
    is_sandbox = "sdbx" in settings.paddle_api_key
    return {
        "provider": "paddle" if settings.paddle_api_key else "stripe",
        "paddle_environment": "sandbox" if is_sandbox else "production",
        "prices": PADDLE_PRICE_IDS,
    }


@router.get("/billing/success")
async def billing_success():
    return HTMLResponse("""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SnapForge — Subscription Active</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}
.card{background:#1e293b;border:1px solid #334155;border-radius:16px;padding:48px;max-width:500px;text-align:center}
h1{font-size:28px;margin-bottom:8px}p{color:#94a3b8;margin-bottom:24px}
.badge{display:inline-block;background:#3b82f620;color:#3b82f6;padding:4px 12px;border-radius:12px;font-size:13px;font-weight:600;margin-bottom:16px}
a{color:#3b82f6;text-decoration:none}a:hover{text-decoration:underline}
</style></head><body><div class="card">
<div class="badge">Subscription Active</div>
<h1>You're all set!</h1>
<p>Your subscription is being processed. You'll receive your API key and plan details shortly via webhook.</p>
<p style="font-size:13px">If you already have an account, your plan has been upgraded automatically.</p>
<p style="margin-top:24px"><a href="/login">Login to Dashboard</a> &middot; <a href="/docs">API Docs</a> &middot; <a href="/">Home</a></p>
</div></body></html>""")


@router.post("/billing/paddle-webhook")
async def paddle_webhook(request: Request):
    payload = await request.body()

    if settings.paddle_webhook_secret:
        sig = request.headers.get("paddle-signature", "")
        if not _verify_paddle_signature(payload, sig, settings.paddle_webhook_secret):
            raise HTTPException(400, "Invalid signature")

    event = json.loads(payload)
    event_type = event.get("event_type", "")
    data = event.get("data", {})

    _init_paddle_prices()

    if event_type == "subscription.created" or event_type == "subscription.updated":
        paddle_customer_id = data.get("customer_id", "")
        subscription_id = data.get("id", "")
        status = data.get("status", "")
        items = data.get("items", [])
        price_id = items[0]["price"]["id"] if items else ""
        tier = PADDLE_TIER_FROM_PRICE.get(price_id, "pro")

        next_billed = data.get("next_billed_at")

        custom_data = data.get("custom_data") or {}
        email = custom_data.get("email", "")

        if not email:
            txn_id = data.get("transaction_id", "")
            if txn_id and settings.paddle_api_key:
                email = _get_email_from_paddle_customer(paddle_customer_id)

        if email:
            customer = get_customer_by_email(email)
            if customer:
                if customer.get("stripe_customer_id") != paddle_customer_id:
                    from snapforge.db import _conn
                    from datetime import datetime, timezone
                    conn = _conn()
                    now = datetime.now(timezone.utc).isoformat()
                    conn.execute(
                        "UPDATE customers SET stripe_customer_id = ?, updated_at = ? WHERE id = ?",
                        (paddle_customer_id, now, customer["id"]),
                    )
                    conn.commit()
                    conn.close()
                upgrade_customer(paddle_customer_id, tier)
                customer = get_customer_by_email(email)
            else:
                customer = create_customer(email, stripe_customer_id=paddle_customer_id, tier=tier)

            if subscription_id and price_id:
                create_subscription(
                    customer["id"], subscription_id, price_id,
                    period_end=next_billed,
                )

    elif event_type == "subscription.canceled":
        paddle_customer_id = data.get("customer_id", "")
        customer = get_customer_by_stripe_id(paddle_customer_id)
        if customer:
            upgrade_customer(paddle_customer_id, "free")

    elif event_type == "transaction.completed":
        custom_data = data.get("custom_data") or {}
        email = custom_data.get("email", "")
        paddle_customer_id = data.get("customer_id", "")
        items = data.get("items", [])
        price_id = items[0]["price"]["id"] if items else ""
        tier = PADDLE_TIER_FROM_PRICE.get(price_id, "pro")

        if email:
            customer = get_customer_by_email(email)
            if not customer:
                customer = create_customer(email, stripe_customer_id=paddle_customer_id, tier=tier)
            elif customer.get("stripe_customer_id") != paddle_customer_id:
                from snapforge.db import _conn
                from datetime import datetime, timezone
                conn = _conn()
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "UPDATE customers SET stripe_customer_id = ?, updated_at = ? WHERE id = ?",
                    (paddle_customer_id, now, customer["id"]),
                )
                conn.commit()
                conn.close()
                upgrade_customer(paddle_customer_id, tier)

    return {"status": "ok"}


def _verify_paddle_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header:
        return False
    parts = {}
    for part in signature_header.split(";"):
        if "=" in part:
            key, val = part.split("=", 1)
            parts[key] = val

    ts = parts.get("ts", "")
    h1 = parts.get("h1", "")
    if not ts or not h1:
        return False

    signed_payload = f"{ts}:{payload.decode()}"
    expected = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(h1, expected)


def _get_email_from_paddle_customer(paddle_customer_id: str) -> str:
    try:
        import urllib.request
        base = "https://sandbox-api.paddle.com" if "sdbx" in settings.paddle_api_key else "https://api.paddle.com"
        req = urllib.request.Request(
            f"{base}/customers/{paddle_customer_id}",
            headers={"Authorization": f"Bearer {settings.paddle_api_key}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("data", {}).get("email", "")
    except Exception:
        return ""
