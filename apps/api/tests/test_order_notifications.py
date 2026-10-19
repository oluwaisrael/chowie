from types import SimpleNamespace
import pytest

from oriade.modules.notifications import orders
from oriade.shared.errors import Problem


def test_order_email_requires_resend_configuration_for_manual_send(monkeypatch):
    monkeypatch.setattr(
        orders,
        "settings",
        lambda: SimpleNamespace(resend_api_key="", order_email_from="", app_origin="http://localhost:3000"),
    )
    order = SimpleNamespace(email="guest@example.com")
    assert orders.send_order_email(order) is False
    with pytest.raises(Problem, match="RESEND_API_KEY"):
        orders.send_order_email(order, required=True)


def test_order_email_posts_to_resend_and_escapes_customer_content(monkeypatch):
    monkeypatch.setattr(
        orders,
        "settings",
        lambda: SimpleNamespace(
            resend_api_key="re_test_secret",
            order_email_from="Óriade <orders@example.com>",
            app_origin="http://localhost:3000",
        ),
    )
    order = SimpleNamespace(
        email="guest@example.com", name="A <script>customer</script>", reference="ORD-2026-TEST",
        status="CONFIRMED", total=125000,
    )
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"id":"email_123"}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["payload"] = request.data.decode()
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(orders, "urlopen", fake_urlopen)
    assert orders.send_order_email(order)
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["authorization"] == "Bearer re_test_secret"
    assert "&lt;script&gt;customer&lt;/script&gt;" in captured["payload"]
    assert captured["timeout"] == 12
