"""Paystack hosted-checkout integration. Payment confirmation always comes from Paystack."""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select

from oriade.shared.config import settings
from oriade.shared.errors import Problem
from oriade.shared.models import Payment


def _request(path, payload=None):
    secret = settings().paystack_secret_key
    if not secret:
        raise Problem("Online payments are not configured yet. Add PAYSTACK_SECRET_KEY to the API environment.", 503)
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        f"https://api.paystack.co{path}",
        data=body,
        headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise Problem("Paystack could not be reached. Please try again.", 502) from exc
    if not result.get("status"):
        raise Problem("Paystack could not process this payment. Please try again.", 502)
    return result["data"]


def initialize(db, order, email=None):
    if order.payment_method != "paystack":
        raise Problem("This order is set to pay on delivery.", 409)
    if order.status == "PENDING_CONFIRMATION":
        raise Problem("The restaurant must confirm your order before you pay.", 409)
    if order.status in {"CANCELLED", "COMPLETED"}:
        raise Problem("This order is no longer eligible for payment.", 409)
    payer_email = str(email) if email else order.email
    if not payer_email:
        raise Problem("Add an email address to your checkout details before paying online.", 409)
    if db.scalar(select(Payment).where(Payment.order_id == order.id, Payment.status == "success")):
        raise Problem("This order has already been paid.", 409)
    previous = db.scalar(
        select(Payment).where(Payment.order_id == order.id, Payment.status == "pending")
        .order_by(Payment.created_at.desc())
    )
    if previous and previous.authorization_url:
        return {"authorization_url": previous.authorization_url, "reference": previous.provider_reference}

    reference = f"oriade-{order.reference}-{secrets.token_hex(8)}"
    data = _request(
        "/transaction/initialize",
        {
            "email": payer_email,
            "amount": str(order.total),
            "currency": settings().paystack_currency,
            "reference": reference,
            "callback_url": f"{settings().app_origin}/orders/{order.reference}",
            "metadata": {"order_reference": order.reference},
        },
    )
    if data.get("reference") != reference or not str(data.get("authorization_url", "")).startswith("https://checkout.paystack.com/"):
        raise Problem("Paystack returned an invalid checkout link. Please try again.", 502)
    payment = Payment(
        order_id=order.id,
        provider_reference=reference,
        authorization_url=data["authorization_url"],
        amount=order.total,
        currency=settings().paystack_currency,
        status="pending",
    )
    order.email = payer_email
    db.add(payment)
    db.commit()
    return {"authorization_url": payment.authorization_url, "reference": payment.provider_reference}


def _mark_success(db, payment, data):
    if (
        data.get("status") != "success"
        or data.get("reference") != payment.provider_reference
        or data.get("amount") != payment.amount
        or data.get("currency") != payment.currency
    ):
        raise Problem("Payment details did not match this order. No payment was recorded.", 409)
    if payment.status != "success":
        payment.status = "success"
        payment.paid_at = datetime.now(timezone.utc)
        db.commit()
        try:
            from oriade.modules.notifications.orders import send_order_email
            from oriade.shared.models import Order

            order = db.get(Order, payment.order_id)
            if order:
                send_order_email(order, "Payment received")
        except Exception:
            pass
    return {"status": "success", "reference": payment.provider_reference}


def verify(db, order, reference):
    payment = db.scalar(
        select(Payment).where(Payment.order_id == order.id, Payment.provider_reference == reference)
    )
    if not payment:
        raise Problem("Payment reference does not belong to this order.", 404)
    if payment.status == "success":
        return {"status": "success", "reference": payment.provider_reference}
    data = _request(f"/transaction/verify/{reference}")
    if data.get("status") != "success":
        if data.get("status") in {"failed", "abandoned"}:
            payment.status = data["status"]
            db.commit()
        return {"status": payment.status, "reference": payment.provider_reference}
    return _mark_success(db, payment, data)


def webhook(db, body, signature):
    secret = settings().paystack_secret_key
    if not secret:
        raise Problem("Payment webhook is not configured.", 503)
    expected = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(expected, signature or ""):
        raise Problem("Invalid Paystack signature.", 401)
    try:
        event = json.loads(body)
    except json.JSONDecodeError as exc:
        raise Problem("Invalid webhook payload.", 400) from exc
    if event.get("event") != "charge.success":
        return {"received": True}
    data = event.get("data") or {}
    payment = db.scalar(select(Payment).where(Payment.provider_reference == data.get("reference")))
    if payment:
        _mark_success(db, payment, data)
    return {"received": True}
