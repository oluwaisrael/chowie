import os

# These tests require a dedicated database, never the application database.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://oriade@127.0.0.1:55432/oriade_test"
)
os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:56379/15")
os.environ["APP_ORIGIN"] = "http://testserver"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from oriade.main import app
from oriade.shared.db import SessionLocal, engine
from oriade.shared.security import redis
from oriade.shared.models import User
from oriade.modules.identity.service import hasher
from oriade.cli import seed


@pytest.fixture
def client():
    assert engine.url.database.endswith("_test"), "Refusing to reset a non-test database"
    with engine.begin() as connection:
        tables = (
            connection.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename != 'alembic_version'"
                )
            )
            .scalars()
            .all()
        )
        if tables:
            connection.execute(text("TRUNCATE " + ",".join('"' + t + '"' for t in tables) + " CASCADE"))
    redis.flushdb()
    seed()
    with SessionLocal() as db:
        for role in ["admin", "operator", "kitchen", "customer"]:
            db.add(
                User(
                    name=role,
                    email=f"{role}@example.com",
                    role=role,
                    password_hash=hasher.hash("test-password-long"),
                )
            )
        db.commit()
    with TestClient(app, headers={"Origin": "http://testserver"}) as client:
        yield client


def sign_in(client, role):
    result = client.post(
        "/auth/login", json={"email": f"{role}@example.com", "password": "test-password-long"}
    )
    assert result.status_code == 200
    client.headers["X-CSRF-Token"] = result.json()["csrf"]
    return result.json()
