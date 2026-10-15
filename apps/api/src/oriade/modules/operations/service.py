from sqlalchemy import select, delete
from oriade.shared.models import User, Session, Location, Inventory, MenuItem
from oriade.shared.errors import Problem
from oriade.modules.audit.service import record


def save_entity(db, actor, model, data, entity_id=None):
    entity = db.get(model, entity_id) if entity_id else model()
    if not entity:
        raise Problem("Record not found.", 404)
    if hasattr(data, "location_id") and not db.get(Location, data.location_id):
        raise Problem("Location not found.")
    for key, value in data.model_dump().items():
        setattr(entity, key, value)
    db.add(entity)
    db.flush()
    record(db, actor, f"{model.__tablename__}.saved", entity.id)
    db.commit()
    return {"id": str(entity.id)}


def update_staff(db, actor, user_id, data):
    if actor.id == user_id:
        raise Problem("You cannot change your own access.")
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise Problem("User not found.", 404)
    user.role, user.active = data.role, data.active
    db.execute(delete(Session).where(Session.user_id == user.id))
    record(db, actor, "staff.access", user.id, data.model_dump())
    db.commit()
    return {"ok": True}


def update_stock(db, actor, item_id, remaining):
    if not db.get(MenuItem, item_id):
        raise Problem("Meal not found.", 404)
    stock = db.scalar(select(Inventory).where(Inventory.item_id == item_id).with_for_update())
    if not stock:
        stock = Inventory(item_id=item_id)
        db.add(stock)
    stock.remaining = remaining
    record(db, actor, "inventory.updated", item_id, {"remaining": remaining})
    db.commit()
    return {"ok": True}
