from sqlalchemy import select, func, case
from oriade.shared.models import Order, OrderItem, StatusHistory, MenuItem, Category


def reports(db):
    counts = dict(db.execute(select(Order.status, func.count()).group_by(Order.status)).all())
    count, value, avg = db.execute(
        select(func.count(), func.coalesce(func.sum(Order.total), 0), func.coalesce(func.avg(Order.total), 0))
    ).one()
    confirmed = db.scalar(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.status.in_(["CONFIRMED", "PREPARING", "READY", "OUT_FOR_DELIVERY", "COMPLETED"])
        )
    )
    popular = db.execute(
        select(OrderItem.name, func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != "CANCELLED")
        .group_by(OrderItem.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(8)
    ).all()
    daily = db.execute(
        select(func.date(Order.created_at), func.count())
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at).desc())
        .limit(30)
    ).all()
    categories = db.execute(
        select(Category.name, func.sum(OrderItem.quantity))
        .join(MenuItem, MenuItem.category_id == Category.id)
        .join(OrderItem, OrderItem.item_id == MenuItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != "CANCELLED")
        .group_by(Category.name)
    ).all()
    times = (
        select(
            StatusHistory.order_id,
            func.min(case((StatusHistory.status == "PREPARING", StatusHistory.created_at))).label("start"),
            func.min(case((StatusHistory.status == "READY", StatusHistory.created_at))).label("end"),
        )
        .group_by(StatusHistory.order_id)
        .subquery()
    )
    preparation = db.scalar(
        select(func.avg(func.extract("epoch", times.c.end - times.c.start) / 60)).where(
            times.c.start.is_not(None), times.c.end.is_not(None)
        )
    )
    return {
        "total_orders": count,
        "submitted_order_value": int(value),
        "confirmed_order_value": int(confirmed),
        "average_order_value": int(avg),
        "counts": counts,
        "popular": [{"name": n, "quantity": int(q)} for n, q in popular],
        "daily": [{"date": str(d), "orders": c} for d, c in daily],
        "categories": [{"name": n, "quantity": int(q)} for n, q in categories],
        "average_preparation_minutes": float(preparation) if preparation else None,
        "collected_revenue": None,
    }
