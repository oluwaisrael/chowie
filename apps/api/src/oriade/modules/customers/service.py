from sqlalchemy import select
from oriade.shared.models import Address
from oriade.shared.errors import Problem


def addresses(db, user):
    return [
        {"id": str(a.id), "label": a.label, "address": a.address, "phone": a.phone}
        for a in db.scalars(select(Address).where(Address.user_id == user.id))
    ]


def save_address(db, user, data):
    if len(addresses(db, user)) >= 10:
        raise Problem("You can save up to 10 addresses.")
    address = Address(user_id=user.id, **data.model_dump())
    db.add(address)
    db.commit()
    return {"id": str(address.id)}


def delete_address(db, user, address_id):
    address = db.get(Address, address_id)
    if not address or address.user_id != user.id:
        raise Problem("Address not found.", 404)
    db.delete(address)
    db.commit()
    return {"ok": True}
