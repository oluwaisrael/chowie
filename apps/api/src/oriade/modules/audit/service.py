from oriade.shared.models import Audit


def record(db, actor, action, target, details=None):
    db.add(
        Audit(actor_id=actor.id if actor else None, action=action, target=str(target), details=details or {})
    )
