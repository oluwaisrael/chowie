import pytest
from oriade.modules.ordering.domain import validate_transition, line_total


@pytest.mark.parametrize(
    "current,target,fulfillment,role",
    [
        ("PENDING_CONFIRMATION", "CONFIRMED", "delivery", "operator"),
        ("CONFIRMED", "PREPARING", "pickup", "kitchen"),
        ("PREPARING", "READY", "pickup", "kitchen"),
        ("READY", "COMPLETED", "pickup", "operator"),
        ("READY", "OUT_FOR_DELIVERY", "delivery", "operator"),
    ],
)
def test_valid_transition(current, target, fulfillment, role):
    validate_transition(current, target, fulfillment, role)


@pytest.mark.parametrize(
    "current,target,fulfillment,role",
    [
        ("PENDING_CONFIRMATION", "CONFIRMED", "delivery", "kitchen"),
        ("PENDING_CONFIRMATION", "READY", "delivery", "admin"),
        ("READY", "OUT_FOR_DELIVERY", "pickup", "admin"),
        ("READY", "COMPLETED", "delivery", "operator"),
        ("COMPLETED", "CANCELLED", "delivery", "admin"),
    ],
)
def test_reject_transition(current, target, fulfillment, role):
    with pytest.raises(ValueError):
        validate_transition(current, target, fulfillment, role)


def test_money_calculation():
    assert line_total(650000, [100000, 250000], 2) == 2000000
    with pytest.raises(ValueError):
        line_total(650000, [], 0)
