from oriade.shared.models import Location, Zone
from oriade.shared.errors import Problem


def validate_fulfillment(db, request):
    location = db.get(Location, request.location_id)
    if not location or not location.active:
        raise Problem("This restaurant location is currently unavailable.")
    if request.fulfillment == "pickup":
        return 0, location.address
    zone = db.get(Zone, request.zone_id) if request.zone_id else None
    if not zone or not zone.active or zone.location_id != location.id:
        raise Problem("Select a valid delivery zone for this restaurant.")
    if not request.address.strip():
        raise Problem("A delivery address is required.")
    return zone.fee, f"{request.address} ({zone.name})"
