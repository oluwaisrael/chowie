from urllib.parse import urlencode
from typing import Protocol
from oriade.shared.config import settings


class MessagingProvider(Protocol):
    """Future Cloud API boundary; click-to-chat does not implement automatic sending."""

    def send(self, recipient: str, template: str, parameters: dict) -> str: ...


def naira(kobo):
    return f"₦{kobo / 100:,.2f}"


def whatsapp_url(order, items):
    lines = ["ÓRIADE — NEW ORDER", "", f"Order: {order.reference}", f"Customer: {order.name}", "", "Items:"]
    for item in items:
        lines.append(
            f"{item.quantity} × {item.name} — {naira(item.unit_price * item.quantity)} ({naira(item.unit_price)} each)"
        )
        if item.modifiers:
            lines.append("  Add-ons: " + ", ".join(m["name"] for m in item.modifiers))
    lines += [
        "",
        f"Subtotal: {naira(order.subtotal)}",
        f"Delivery: {naira(order.delivery_fee)}",
        f"Total: {naira(order.total)}",
        "",
        f"Fulfillment: {order.fulfillment.title()}",
        f"Location: {order.address}",
        f"Phone: {order.phone}",
    ]
    if order.instructions:
        lines.append(f"Instructions: {order.instructions}")
    lines += ["", "Please confirm availability and the next steps for this order."]
    return f"https://wa.me/{settings().whatsapp_number}?" + urlencode({"text": "\n".join(lines)})
