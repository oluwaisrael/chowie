"""Persistence mappings. Business decisions live in module services and pure domain functions."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, CheckConstraint, UniqueConstraint, DateTime, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from oriade.shared.db import Base


def now():
    return datetime.now(timezone.utc)


class Entity:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Entity, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="customer")
    active: Mapped[bool] = mapped_column(default=True)
    __table_args__ = (CheckConstraint("role IN ('customer','operator','kitchen','admin')"),)


class Session(Entity, Base):
    __tablename__ = "sessions"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PasswordReset(Entity, Base):
    __tablename__ = "password_resets"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(default=False)


class Address(Entity, Base):
    __tablename__ = "addresses"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(60))
    address: Mapped[str] = mapped_column(String(500))
    phone: Mapped[str] = mapped_column(String(30))


class Location(Entity, Base):
    __tablename__ = "locations"
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(default=True)


class Zone(Entity, Base):
    __tablename__ = "delivery_zones"
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    fee: Mapped[int] = mapped_column(BigInteger)
    active: Mapped[bool] = mapped_column(default=True)
    __table_args__ = (CheckConstraint("fee >= 0"),)


class Category(Entity, Base):
    __tablename__ = "categories"
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)


class MenuItem(Entity, Base):
    __tablename__ = "menu_items"
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"), index=True)
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(1000))
    price: Mapped[int] = mapped_column(BigInteger)
    image: Mapped[str] = mapped_column(String(1000), default="")
    available: Mapped[bool] = mapped_column(default=True)
    featured: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (CheckConstraint("price >= 0"),)


class Modifier(Entity, Base):
    __tablename__ = "modifiers"
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("menu_items.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column(BigInteger)
    available: Mapped[bool] = mapped_column(default=True)
    __table_args__ = (CheckConstraint("price >= 0"),)


class Inventory(Base):
    __tablename__ = "inventory"
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("menu_items.id"), primary_key=True)
    remaining: Mapped[int | None] = mapped_column(default=None)
    __table_args__ = (CheckConstraint("remaining IS NULL OR remaining >= 0"),)


class Order(Entity, Base):
    __tablename__ = "orders"
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    access_hash: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(500), default="")
    instructions: Mapped[str] = mapped_column(String(500), default="")
    fulfillment: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="PENDING_CONFIRMATION", index=True)
    subtotal: Mapped[int] = mapped_column(BigInteger)
    delivery_fee: Mapped[int] = mapped_column(BigInteger)
    total: Mapped[int] = mapped_column(BigInteger)
    version: Mapped[int] = mapped_column(default=1)
    __table_args__ = (
        CheckConstraint("subtotal >= 0 AND delivery_fee >= 0 AND total = subtotal + delivery_fee"),
        CheckConstraint("fulfillment IN ('delivery','pickup')"),
        CheckConstraint(
            "status IN ('PENDING_CONFIRMATION','CONFIRMED','PREPARING','READY','OUT_FOR_DELIVERY','COMPLETED','CANCELLED')"
        ),
    )


class OrderItem(Entity, Base):
    __tablename__ = "order_items"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("menu_items.id"))
    name: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int]
    unit_price: Mapped[int] = mapped_column(BigInteger)
    modifiers: Mapped[list] = mapped_column(JSON, default=list)
    __table_args__ = (CheckConstraint("quantity > 0 AND unit_price >= 0"),)


class StatusHistory(Entity, Base):
    __tablename__ = "order_status_history"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30))


class Handoff(Entity, Base):
    __tablename__ = "whatsapp_handoffs"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), unique=True)
    initiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Outbox(Entity, Base):
    __tablename__ = "outbox_events"
    topic: Mapped[str] = mapped_column(String(60))
    aggregate_id: Mapped[uuid.UUID]
    payload: Mapped[dict] = mapped_column(JSON)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class Audit(Entity, Base):
    __tablename__ = "audit_logs"
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100))
    target: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Notification(Entity, Base):
    __tablename__ = "notifications"
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("outbox_events.id"), unique=True)
    kind: Mapped[str] = mapped_column(String(60))
    __table_args__ = (UniqueConstraint("event_id", "kind"),)
