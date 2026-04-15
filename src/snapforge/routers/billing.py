from __future__ import annotations

import stripe
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse

from snapforge.config import settings
from snapforge.db import (
    init_db, create_customer, get_customer_by_email,
    get_customer_by_stripe_id, upgrade_customer, create_subscription,
)

router = APIRouter()

PRICE_IDS = {
    "pro": "price_1TMLxiRu294FtgQT1wZJQGC6",
    "business": "price_1TMLxiRu294FtgQTb6vECShG",
}

TIER_FROM_PRICE = {v: k for k, v in PRICE_IDS.items()}


@router.get("/billing/free-key")
async def free_key(email: str = Query(...)):
    existing = get_customer_by_email(email)
    if existing:
        return {"message": "Account already exists. Check your email for your API key.", "api_key": existing["api_key"]}
    customer = create_customer(email, tier="free")
    return {"api_key": customer["api_key"], "tier": "free", "requests_limit": 100}


@router.get("/checkout")
async def checkout(
    plan: str = Query(..., pattern="^(pro|business)$"),
    email: str = Query(...),
):
    stripe.api_key = settings.stripe_secret_key
    price_id = PRICE_IDS.get(plan)
    if not price_id:
        raise HTTPException(400, "Invalid plan")

    base_url = settings.base_url or "https://snapforge-api-production.up.railway.app"

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer_email=email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/#pricing",
    )
    return RedirectResponse(session.url, status_code=303)


@router.get("/billing/success")
async def billing_success(session_id: str = Query(...)):
    stripe.api_key = settings.stripe_secret_key
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.InvalidRequestError:
        return HTMLResponse(
            "<html><body style='background:#0f172a;color:#e2e8f0;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif'>"
            "<div style='text-align:center'><h2>Session not found</h2><p style='color:#94a3b8'>The checkout session may have expired. <a href='/#pricing' style='color:#3b82f6'>Try again</a></p></div></body></html>",
            status_code=400,
        )

    email = session.customer_email or session.customer_details.email
    stripe_customer_id = session.customer
    subscription_id = session.subscription

    sub = stripe.Subscription.retrieve(subscription_id)
    import json
    sub_data = json.loads(str(sub))
    price_id = sub_data["items"]["data"][0]["price"]["id"]
    tier = TIER_FROM_PRICE.get(price_id, "pro")

    customer = get_customer_by_email(email)
    if customer:
        upgrade_customer(stripe_customer_id, tier)
        customer = get_customer_by_email(email)
    else:
        customer = create_customer(email, stripe_customer_id=stripe_customer_id, tier=tier)

    period_end = sub_data.get("current_period_end")
    create_subscription(
        customer["id"], subscription_id, price_id,
        period_end=str(period_end) if period_end else None,
    )

    api_key = customer["api_key"]
    limit = customer["requests_limit"]
    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SnapForge — Subscription Active</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}}
.card{{background:#1e293b;border:1px solid #334155;border-radius:16px;padding:48px;max-width:500px;text-align:center}}
h1{{font-size:28px;margin-bottom:8px}}p{{color:#94a3b8;margin-bottom:24px}}
.key{{background:#0d1117;border:1px solid #334155;border-radius:8px;padding:16px;font-family:monospace;font-size:14px;word-break:break-all;margin-bottom:24px;color:#3b82f6}}
.badge{{display:inline-block;background:#3b82f620;color:#3b82f6;padding:4px 12px;border-radius:12px;font-size:13px;font-weight:600;margin-bottom:16px}}
a{{color:#3b82f6;text-decoration:none}}a:hover{{text-decoration:underline}}
</style></head><body><div class="card">
<div class="badge">{tier.upper()} Plan</div>
<h1>You're all set!</h1>
<p>{limit:,} requests/month</p>
<p style="color:#e2e8f0;font-size:14px;margin-bottom:8px">Your API Key:</p>
<div class="key">{api_key}</div>
<p style="color:#f59e0b;font-size:13px;font-weight:600">⚠️ Please save this key! You'll need it for every API call.</p>
<p style="font-size:13px;margin-top:8px">Forgot your key? Use <a href="/forgot-key">Forgot API Key</a> to recover it via email.</p>
<p style="margin-top:24px"><a href="/login">Login to Dashboard</a> &middot; <a href="/docs">API Docs</a> &middot; <a href="/">Home</a></p>
</div></body></html>""")


@router.post("/billing/webhook")
async def stripe_webhook(request: Request):
    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    if settings.stripe_webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(400, "Invalid signature")
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")

    if event_type == "customer.subscription.updated":
        sub = event["data"]["object"]
        stripe_customer_id = sub["customer"]
        price_id = sub["items"]["data"][0]["price"]["id"]
        tier = TIER_FROM_PRICE.get(price_id, "pro")

        customer = get_customer_by_stripe_id(stripe_customer_id)
        if customer:
            upgrade_customer(stripe_customer_id, tier)

    elif event_type == "customer.subscription.deleted":
        sub = event["data"]["object"]
        stripe_customer_id = sub["customer"]
        customer = get_customer_by_stripe_id(stripe_customer_id)
        if customer:
            upgrade_customer(stripe_customer_id, "free")

    return {"status": "ok"}
