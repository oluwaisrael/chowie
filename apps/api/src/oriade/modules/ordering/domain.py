"""Pure ordering rules: no framework, persistence or integration imports."""

TRANSITIONS = {
    "PENDING_CONFIRMATION": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"PREPARING", "CANCELLED"},
    "PREPARING": {"READY", "CANCELLED"},
    "READY": {"OUT_FOR_DELIVERY", "COMPLETED", "CANCELLED"},
    "OUT_FOR_DELIVERY": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def validate_transition(current: str, target: str, fulfillment: str, role: str):
    if target not in TRANSITIONS.get(current, set()):
        raise ValueError("This order status transition is not allowed.")
    if role == "kitchen" and (current, target) not in {("CONFIRMED", "PREPARING"), ("PREPARING", "READY")}:
        raise ValueError("Kitchen staff can only start preparation and mark orders ready.")
    if target == "OUT_FOR_DELIVERY" and fulfillment != "delivery":
        raise ValueError("Pickup orders cannot go out for delivery.")
    if current == "READY" and target == "COMPLETED" and fulfillment != "pickup":
        raise ValueError("Delivery orders must be dispatched before completion.")


def line_total(price: int, modifiers: list[int], quantity: int) -> int:
    if price < 0 or any(p < 0 for p in modifiers) or not 1 <= quantity <= 20:
        raise ValueError("Invalid price or quantity.")
    return (price + sum(modifiers)) * quantity
