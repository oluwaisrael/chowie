import secrets
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs
from sqlalchemy import select, func
from fastapi.testclient import TestClient
from oriade.main import app
from oriade.shared.db import SessionLocal
from oriade.shared.models import Order, Inventory, MenuItem, Outbox, Notification, Session
from oriade.workers.tasks import publish_outbox
from conftest import sign_in


def checkout_data(client):
    catalog = client.get("/catalog").json()
    item = catalog["items"][0]
    payload = {
        "name": "Test Customer",
        "phone": "08066514361",
        "location_id": item["location_id"],
        "zone_id": catalog["zones"][0]["id"],
        "fulfillment": "delivery",
        "address": "12 Test Street",
        "instructions": "Less pepper, please.",
        "items": [{"item_id": item["id"], "quantity": 2, "modifiers": [item["modifiers"][0]["id"]]}],
    }
    headers = {"Idempotency-Key": str(uuid4()), "X-Order-Token": secrets.token_urlsafe(32)}
    return payload, headers, item, catalog


def test_checkout_snapshot_idempotency_and_handoff(client):
    payload, headers, item, catalog = checkout_data(client)
    response = client.post("/orders", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    order = response.json()
    assert order["total"] == (item["price"] + item["modifiers"][0]["price"]) * 2 + catalog["zones"][0]["fee"]
    assert order["status"] == "PENDING_CONFIRMATION"
    assert client.post("/orders", json=payload, headers=headers).json()["reference"] == order["reference"]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 1
        meal = db.get(MenuItem, __import__("uuid").UUID(item["id"]))
        meal.price += 10000
        db.commit()
    path = "/orders/" + order["reference"]
    assert client.get(path).status_code == 404
    assert client.get(path, headers={"X-Order-Token": "wrong"}).status_code == 404
    assert client.get(path, headers=headers).json()["total"] == order["total"]
    handoff = client.post(path + "/handoff", headers=headers)
    assert handoff.json()["status"] == "PENDING_CONFIRMATION"
    assert client.post(path + "/handoff", headers=headers).status_code == 200
    parsed = urlparse(order["whatsapp_url"])
    assert parsed.netloc == "wa.me" and parsed.path == "/2348066514361"
    message = parse_qs(parsed.query)["text"][0]
    assert order["reference"] in message and "Extra grilled chicken" in message and "Less pepper" in message
    assert headers["X-Order-Token"] not in message and item["id"] not in message
    payload["name"] = "Changed name"
    assert client.post("/orders", json=payload, headers=headers).status_code == 409


def test_authorization_csrf_and_origin(client):
    payload, headers, *_ = checkout_data(client)
    reference = client.post("/orders", json=payload, headers=headers).json()["reference"]
    assert client.get("/admin/reports").status_code == 401
    sign_in(client, "customer")
    assert client.get("/admin/reports").status_code == 403
    assert client.get("/orders/" + reference).status_code == 404
    assert client.post("/auth/logout", headers={"X-CSRF-Token": "bad"}).status_code == 403
    assert client.post("/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_staff_lifecycle_privacy_and_optimistic_lock(client):
    payload, headers, *_ = checkout_data(client)
    reference = client.post("/orders", json=payload, headers=headers).json()["reference"]
    sign_in(client, "kitchen")
    assert client.get("/orders").json() == []
    assert (
        client.patch(f"/orders/{reference}/status", json={"status": "CONFIRMED", "version": 1}).status_code
        == 409
    )
    sign_in(client, "operator")
    assert (
        client.patch(f"/orders/{reference}/status", json={"status": "CONFIRMED", "version": 1}).status_code
        == 200
    )
    assert (
        client.patch(f"/orders/{reference}/status", json={"status": "PREPARING", "version": 1}).status_code
        == 409
    )
    sign_in(client, "kitchen")
    kitchen = client.get("/orders").json()[0]
    assert "phone" not in kitchen and "address" not in kitchen and "name" not in kitchen
    assert (
        client.patch(f"/orders/{reference}/status", json={"status": "PREPARING", "version": 2}).status_code
        == 200
    )
    assert (
        client.patch(f"/orders/{reference}/status", json={"status": "READY", "version": 3}).status_code == 200
    )
    sign_in(client, "operator")
    assert (
        client.patch(f"/orders/{reference}/status", json={"status": "COMPLETED", "version": 4}).status_code
        == 409
    )
    assert (
        client.patch(
            f"/orders/{reference}/status", json={"status": "OUT_FOR_DELIVERY", "version": 4}
        ).status_code
        == 200
    )
    assert (
        client.patch(f"/orders/{reference}/status", json={"status": "COMPLETED", "version": 5}).status_code
        == 200
    )
    assert client.get("/admin/reports").json()["counts"]["COMPLETED"] == 1
    assert client.get("/admin/reports").json()["collected_revenue"] is None


def test_stock_duplicate_modifiers_and_untrusted_prices(client):
    payload, headers, item, _ = checkout_data(client)
    payload["total"] = 1
    assert client.post("/orders", json=payload, headers=headers).status_code == 422
    del payload["total"]
    payload["items"][0]["modifiers"] *= 2
    assert client.post("/orders", json=payload, headers=headers).status_code == 422
    payload["items"][0]["modifiers"] = []
    with SessionLocal() as db:
        stock = db.get(Inventory, __import__("uuid").UUID(item["id"]))
        stock.remaining = 1
        db.commit()
    assert client.post("/orders", json=payload, headers=headers).status_code == 409
    with SessionLocal() as db:
        assert db.get(Inventory, __import__("uuid").UUID(item["id"])).remaining == 1
        assert db.scalar(select(func.count()).select_from(Order)) == 0


def test_concurrent_duplicate_checkout(client):
    payload, headers, *_ = checkout_data(client)

    def submit(_):
        with TestClient(app, headers={"Origin": "http://testserver", **headers}) as other:
            return other.post("/orders", json=payload)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(submit, range(4)))
    assert all(r.status_code == 201 for r in results)
    assert len({r.json()["reference"] for r in results}) == 1
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 1


def test_outbox_consumer_idempotency(client):
    payload, headers, *_ = checkout_data(client)
    client.post("/orders", json=payload, headers=headers)
    assert publish_outbox() == 1
    assert publish_outbox() == 0
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Notification)) == 1
        assert db.scalar(select(Outbox)).published_at is not None


def test_staff_revocation_and_address_ownership(client):
    user = sign_in(client, "customer")["user"]
    address = client.post(
        "/addresses", json={"label": "Home", "address": "123 Test Street", "phone": "08066514361"}
    ).json()
    sign_in(client, "operator")
    assert client.delete("/addresses/" + address["id"]).status_code == 404
    sign_in(client, "admin")
    assert (
        client.patch("/admin/users/" + user["id"], json={"role": "customer", "active": False}).status_code
        == 200
    )
    with SessionLocal() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Session)
                .where(Session.user_id == __import__("uuid").UUID(user["id"]))
            )
            == 0
        )
    assert (
        client.post(
            "/auth/login", json={"email": "customer@example.com", "password": "test-password-long"}
        ).status_code
        == 401
    )
