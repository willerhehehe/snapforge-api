from __future__ import annotations

import stripe
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse

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
    session = stripe.checkout.Session.retrieve(session_id)

    email = session.customer_email or session.customer_details.email
    stripe_customer_id = session.customer
    subscription_id = session.subscription

    sub = stripe.Subscription.retrieve(subscription_id)
    price_id = sub["items"]["data"][0]["price"]["id"]
    tier = TIER_FROM_PRICE.get(price_id, "pro")

    customer = get_customer_by_email(email)
    if customer:
        upgrade_customer(stripe_customer_id, tier)
        customer = get_customer_by_email(email)
    else:
        customer = create_customer(email, stripe_customer_id=stripe_customer_id, tier=tier)

    create_subscription(
        customer["id"], subscription_id, price_id,
        period_end=sub["current_period_end"],
    )

    return JSONResponse({
        "status": "success",
        "tier": tier,
        "api_key": customer["api_key"],
        "requests_limit": customer["requests_limit"],
        "message": f"Welcome! Your API key is: {customer['api_key']}",
    })


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
