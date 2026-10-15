from sqlalchemy import select
from oriade.shared.models import MenuItem, Modifier, Category, Location, Zone, Inventory
from oriade.shared.errors import Problem
from oriade.modules.audit.service import record


def catalog(db):
    items = db.scalars(select(MenuItem).order_by(MenuItem.created_at)).all()
    modifiers = db.scalars(select(Modifier)).all()
    stock = {str(s.item_id): s.remaining for s in db.scalars(select(Inventory)).all()}
    return {
        "items": [
            {
                "id": str(i.id),
                "name": i.name,
                "description": i.description,
                "price": i.price,
                "image": i.image,
                "available": i.available and stock.get(str(i.id)) != 0,
                "featured": i.featured,
                "category_id": str(i.category_id),
                "location_id": str(i.location_id),
                "modifiers": [
                    {"id": str(m.id), "name": m.name, "price": m.price, "available": m.available}
                    for m in modifiers
                    if m.item_id == i.id
                ],
            }
            for i in items
        ],
        "categories": [
            {"id": str(c.id), "name": c.name, "slug": c.slug}
            for c in db.scalars(select(Category).order_by(Category.created_at))
        ],
        "locations": [
            {"id": str(i.id), "name": i.name, "address": i.address, "active": i.active}
            for i in db.scalars(select(Location))
        ],
        "zones": [
            {
                "id": str(z.id),
                "name": z.name,
                "fee": z.fee,
                "location_id": str(z.location_id),
                "active": z.active,
            }
            for z in db.scalars(select(Zone))
        ],
    }


def save_item(db, actor, data, item_id=None):
    item = db.get(MenuItem, item_id) if item_id else MenuItem()
    if not item:
        raise Problem("Meal not found.", 404)
    if not db.get(Category, data.category_id) or not db.get(Location, data.location_id):
        raise Problem("Select a valid category and location.")
    for key, value in data.model_dump(exclude={"modifiers"}).items():
        setattr(item, key, value)
    db.add(item)
    db.flush()
    existing = {str(m.id): m for m in db.scalars(select(Modifier).where(Modifier.item_id == item.id))}
    keep = set()
    for m in data.modifiers:
        modifier = existing.get(str(m.id)) if m.id else Modifier(item_id=item.id)
        if modifier is None:
            raise Problem("Modifier does not belong to this meal.")
        modifier.name, modifier.price, modifier.available = m.name, m.price, m.available
        db.add(modifier)
        db.flush()
        keep.add(str(modifier.id))
    for mid, m in existing.items():
        if mid not in keep:
            m.available = False
    if not db.get(Inventory, item.id):
        db.add(Inventory(item_id=item.id))
    record(db, actor, "catalog.saved", item.id)
    db.commit()
    return {"id": str(item.id)}
