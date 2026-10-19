import pytest
import hashlib
import hmac
import json
from types import SimpleNamespace
from oriade.modules.ordering.domain import validate_transition, line_total
from oriade.modules.ordering import payments
from oriade.shared.errors import Problem


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


def test_paystack_payment_is_only_marked_success_for_exact_order_amount():
    class Session:
        committed = False

        def commit(self):
            self.committed = True

    session = Session()
    payment = SimpleNamespace(
        status="pending", provider_reference="oriade-ORD-1-abc", amount=12500,
        currency="NGN", paid_at=None,
    )
    result = payments._mark_success(session, payment, {
        "status": "success", "reference": payment.provider_reference,
        "amount": 12500, "currency": "NGN",
    })
    assert result["status"] == payment.status == "success"
    assert session.committed and payment.paid_at is not None

    payment.status = "pending"
    with pytest.raises(Problem, match="did not match"):
        payments._mark_success(session, payment, {
            "status": "success", "reference": payment.provider_reference,
            "amount": 1, "currency": "NGN",
        })
    assert payment.status == "pending"


def test_paystack_webhook_checks_hmac_signature(monkeypatch):
    monkeypatch.setattr(payments, "settings", lambda: SimpleNamespace(paystack_secret_key="sk_test_unit"))
    body = json.dumps({"event": "transfer.failed"}).encode()
    signature = hmac.new(b"sk_test_unit", body, hashlib.sha512).hexdigest()

    class Session:
        def scalar(self, _query):
            return None

    assert payments.webhook(Session(), body, signature) == {"received": True}
    with pytest.raises(Problem, match="Invalid Paystack signature"):
        payments.webhook(Session(), body, "not-a-valid-signature")
