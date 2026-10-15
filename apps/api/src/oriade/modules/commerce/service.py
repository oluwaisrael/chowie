from sqlalchemy import select
from oriade.shared.models import MenuItem, Modifier, Inventory
from oriade.shared.errors import Problem
from oriade.modules.ordering.domain import line_total


def price_lines(db, lines, location_id):
    ids = sorted({line.item_id for line in lines}, key=str)
    items = {
        i.id: i
        for i in db.scalars(
            select(MenuItem).where(MenuItem.id.in_(ids)).order_by(MenuItem.id).with_for_update()
        )
    }
    inventory = {
        i.item_id: i
        for i in db.scalars(
            select(Inventory).where(Inventory.item_id.in_(ids)).order_by(Inventory.item_id).with_for_update()
        )
    }
    mods = {m.id: m for m in db.scalars(select(Modifier).where(Modifier.item_id.in_(ids)).with_for_update())}
    snapshots = []
    for line in lines:
        item = items.get(line.item_id)
        if not item or not item.available or item.location_id != location_id:
            raise Problem("A selected meal is unavailable at this location.", 409)
        selected = []
        for mid in line.modifiers:
            m = mods.get(mid)
            if not m or not m.available or m.item_id != item.id:
                raise Problem("A selected add-on is no longer available.", 409)
            selected.append({"id": str(m.id), "name": m.name, "price": m.price})
        stock = inventory.get(item.id)
        if stock and stock.remaining is not None:
            if stock.remaining < line.quantity:
                raise Problem(f"Not enough portions of {item.name} are available.", 409)
            stock.remaining -= line.quantity
        total = line_total(item.price, [m["price"] for m in selected], line.quantity)
        snapshots.append(
            {
                "item_id": item.id,
                "name": item.name,
                "quantity": line.quantity,
                "unit_price": total // line.quantity,
                "modifiers": selected,
            }
        )
    return snapshots
