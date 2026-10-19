"""Resend-backed order emails. Email delivery is best-effort for status changes."""

import html
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from oriade.shared.config import settings
from oriade.shared.errors import Problem


def send_order_email(order, status_label=None, required=False):
    config = settings()
    if not order.email:
        if required:
            raise Problem("This order has no customer email address.", 409)
        return False
    if not config.resend_api_key or not config.order_email_from:
        if required:
            raise Problem("Order email is not configured. Add RESEND_API_KEY and ORDER_EMAIL_FROM to the API environment.", 503)
        return False
    status = status_label or order.status.replace("_", " ").title()
    reference = html.escape(order.reference)
    customer = html.escape(order.name)
    safe_status = html.escape(status)
    text = (
        f"Hello {order.name},\n\nYour Óriade order {order.reference} is now {status}.\n"
        f"Order total: NGN {order.total / 100:,.2f}\n\nThank you for choosing Óriade."
    )
    payload = {
        "from": config.order_email_from,
        "to": [order.email],
        "subject": f"Óriade order {order.reference}: {status}",
        "text": text,
        "html": (
            f"<main style='font-family:Arial,sans-serif;color:#1d2b23'>"
            f"<h1>Good food, great company.</h1><p>Hello {customer},</p>"
            f"<p>Your order <strong>{reference}</strong> is now <strong>{safe_status}</strong>.</p>"
            f"<p>Order total: NGN {order.total / 100:,.2f}</p>"
            f"<p>Thank you for choosing Óriade.</p></main>"
        ),
    }
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {config.resend_api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            result = json.loads(response.read())
        if not result.get("id"):
            raise ValueError("Resend returned no email id")
        return True
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        if required:
            raise Problem("Resend could not send this order email. Check the Resend API key and sender domain.", 502) from exc
        return False
