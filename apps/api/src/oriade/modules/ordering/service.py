import json
from collections import defaultdict
import secrets
from sqlalchemy import select, text
from oriade.shared.models import Order, OrderItem, StatusHistory, Handoff, Outbox, Inventory, now
from oriade.shared.errors import Problem
from oriade.modules.identity.service import digest
from oriade.modules.commerce.service import price_lines
from oriade.modules.fulfillment.service import validate_fulfillment
from oriade.modules.notifications.whatsapp import whatsapp_url
from oriade.modules.ordering.domain import validate_transition
from oriade.modules.audit.service import record


def event(db, order, topic):
    db.add(
        Outbox(
            topic=topic,
            aggregate_id=order.id,
            payload={"reference": order.reference, "status": order.status, "version": order.version},
        )
    )


def create_order(db, request, key, access, user):
    # Serialize matching keys across API processes without holding a process-local lock.
    lock = int.from_bytes(bytes.fromhex(digest(key))[:8], signed=True)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
    request_hash = digest(json.dumps(request.model_dump(mode="json"), sort_keys=True))
    existing = db.scalar(select(Order).where(Order.idempotency_key == key))
    if existing:
        if (
            existing.request_hash != request_hash
            or existing.access_hash != digest(access)
            or existing.user_id != (user.id if user else None)
        ):
            raise Problem("This checkout key was already used. Review your order before retrying.", 409)
        return snapshot(db, existing)
    fee, address = validate_fulfillment(db, request)
    lines = price_lines(db, request.items, request.location_id)
    subtotal = sum(i["unit_price"] * i["quantity"] for i in lines)
    order = Order(
        reference="ORD-" + now().strftime("%Y") + "-" + secrets.token_hex(6).upper(),
        user_id=user.id if user else None,
        location_id=request.location_id,
        idempotency_key=key,
        request_hash=request_hash,
        access_hash=digest(access),
        name=request.name,
        email=str(request.email) if request.email else (user.email if user else None),
        phone=request.phone,
        address=address,
        instructions=request.instructions,
        fulfillment=request.fulfillment,
        payment_method=request.payment_method,
        subtotal=subtotal,
        delivery_fee=fee,
        total=subtotal + fee,
    )
    db.add(order)
    db.flush()
    db.add_all([OrderItem(order_id=order.id, **line) for line in lines])
    db.add(StatusHistory(order_id=order.id, status=order.status))
    db.add(Handoff(order_id=order.id))
    event(db, order, "OrderCreated")
    db.commit()
    return snapshot(db, order)


def authorized_order(db, reference, user, access):
    order = db.scalar(select(Order).where(Order.reference == reference))
    allowed = order and (
        (user and (user.role in {"admin", "operator", "kitchen"} or order.user_id == user.id))
        or (access and secrets.compare_digest(order.access_hash, digest(access)))
    )
    if not allowed:
        raise Problem("Order not found or access has expired.", 404)
    return order


def snapshot(db, order, kitchen=False, items=None, history=None):
    if items is None:
        items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    if history is None:
        history = db.scalars(
            select(StatusHistory).where(StatusHistory.order_id == order.id).order_by(StatusHistory.created_at)
        ).all()
    result = {
        "reference": order.reference,
        "status": order.status,
        "version": order.version,
        "created_at": order.created_at.isoformat(),
        "fulfillment": order.fulfillment,
        "instructions": order.instructions,
        "items": [
            {"name": i.name, "quantity": i.quantity, "unit_price": i.unit_price, "modifiers": i.modifiers}
            for i in items
        ],
        "history": [{"status": h.status, "at": h.created_at.isoformat()} for h in history],
    }
    if not kitchen:
        result.update(
            {
                "name": order.name,
                "phone": order.phone,
                "email": order.email,
                "payment_status": _payment_status(db, order),
                "payment_method": order.payment_method,
                "address": order.address,
                "subtotal": order.subtotal,
                "delivery_fee": order.delivery_fee,
                "total": order.total,
                "whatsapp_url": whatsapp_url(order, items),
            }
        )
    return result


def _payment_status(db, order):
    if order.payment_method == "pay_on_delivery":
        return "pay_on_delivery"
    from oriade.shared.models import Payment

    payment = db.scalar(
        select(Payment).where(Payment.order_id == order.id).order_by(Payment.created_at.desc())
    )
    return payment.status if payment else "unpaid"


def initiate_handoff(db, order):
    handoff = db.scalar(select(Handoff).where(Handoff.order_id == order.id).with_for_update())
    if not handoff.initiated_at:
        handoff.initiated_at = now()
        event(db, order, "WhatsAppHandoffInitiated")
        db.commit()
    return {"initiated": True, "status": order.status}


def transition(db, reference, actor, status, version):
    order = db.scalar(select(Order).where(Order.reference == reference).with_for_update())
    if not order:
        raise Problem("Order not found.", 404)
    if order.version != version:
        raise Problem("This order changed. Refresh and try again.", 409)
    try:
        validate_transition(order.status, status, order.fulfillment, actor.role)
    except ValueError as e:
        raise Problem(str(e), 409)
    if status == "CANCELLED":
        lines = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        for line in sorted(lines, key=lambda i: str(i.item_id)):
            stock = db.scalar(select(Inventory).where(Inventory.item_id == line.item_id).with_for_update())
            if stock and stock.remaining is not None:
                stock.remaining += line.quantity
    order.status, order.version = status, order.version + 1
    db.add(StatusHistory(order_id=order.id, actor_id=actor.id, status=status))
    record(db, actor, "order.status", order.reference, {"status": status})
    event(db, order, "Order" + status.title().replace("_", ""))
    db.commit()
    try:
        from oriade.modules.notifications.orders import send_order_email

        send_order_email(order)
    except Exception:
        # A notification failure must never undo a committed kitchen/order update.
        pass
    return snapshot(db, order, actor.role == "kitchen")


def list_orders(db, actor):
    statement = select(Order).order_by(Order.created_at.desc()).limit(100)
    if actor.role == "customer":
        statement = statement.where(Order.user_id == actor.id)
    if actor.role == "kitchen":
        statement = statement.where(Order.status.in_(["CONFIRMED", "PREPARING", "READY"]))
    orders = db.scalars(statement).all()
    ids = [order.id for order in orders]
    items, history = defaultdict(list), defaultdict(list)
    for item in db.scalars(
        select(OrderItem).where(OrderItem.order_id.in_(ids)).order_by(OrderItem.created_at)
    ):
        items[item.order_id].append(item)
    for entry in db.scalars(
        select(StatusHistory).where(StatusHistory.order_id.in_(ids)).order_by(StatusHistory.created_at)
    ):
        history[entry.order_id].append(entry)
    return [snapshot(db, o, actor.role == "kitchen", items[o.id], history[o.id]) for o in orders]
