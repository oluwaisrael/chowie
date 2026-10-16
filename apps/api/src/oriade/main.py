import asyncio
import json
from uuid import UUID, uuid4
from fastapi import FastAPI, Depends, Request, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from oriade.shared.config import settings
from oriade.shared.db import db_session, SessionLocal
from oriade.shared.models import User, Category, Location, Zone, Audit
from oriade.shared.errors import Problem
from oriade.shared import schemas as s
from oriade.shared.security import principal, require, rate_limit
from oriade.modules.identity import service as identity
from oriade.modules.catalog import service as catalog
from oriade.modules.ordering import service as ordering
from oriade.modules.customers import service as customers
from oriade.modules.operations import service as operations
from oriade.modules.reporting.service import reports

app = FastAPI(title="Óriade API", version="0.1.0")
if settings().sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(dsn=settings().sentry_dsn, send_default_pii=False, traces_sample_rate=0.1)
if __import__("os").getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)


@app.exception_handler(Problem)
async def problem_handler(request, exc):
    return JSONResponse({"detail": exc.message}, status_code=exc.status)


@app.exception_handler(IntegrityError)
async def integrity_handler(request, exc):
    return JSONResponse({"detail": "This change conflicts with an existing record."}, status_code=409)


@app.middleware("http")
async def protect(request, call_next):
    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and request.headers.get("origin") != settings().app_origin
    ):
        return JSONResponse({"detail": "Request origin is not permitted."}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Request-ID"] = str(uuid4())
    return response


@app.get("/health")
def health(db=Depends(db_session)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/catalog")
def get_catalog(db=Depends(db_session)):
    return catalog.catalog(db)


@app.post("/auth/register", status_code=201)
def register(data: s.Register, request: Request, db=Depends(db_session)):
    rate_limit(request, "auth", 15)
    return identity.public_user(identity.register(db, data.name, str(data.email), data.password))


@app.post("/auth/login")
def login(data: s.Login, request: Request, response: Response, db=Depends(db_session)):
    rate_limit(request, "auth", 15)
    user, session, token = identity.login(db, str(data.email), data.password)
    response.set_cookie(
        "oriade_session",
        token,
        httponly=True,
        secure=settings().environment == "production",
        samesite="lax",
        max_age=settings().session_days * 86400,
        path="/",
    )
    return {"user": identity.public_user(user), "csrf": session.csrf}


@app.get("/auth/me")
def me(request: Request, db=Depends(db_session)):
    user, session = identity.authenticate(db, request.cookies.get("oriade_session"))
    if not user:
        raise Problem("Please sign in to continue.", 401)
    return {"user": identity.public_user(user), "csrf": session.csrf}


@app.post("/auth/logout")
def logout(request: Request, response: Response, user=Depends(require()), db=Depends(db_session)):
    identity.logout(db, request.cookies.get("oriade_session", ""))
    response.delete_cookie("oriade_session", path="/")
    return {"ok": True}


@app.post("/auth/forgot-password")
def forgot(data: s.ResetRequest, request: Request, db=Depends(db_session)):
    rate_limit(request, "reset", 5)
    return identity.request_reset(db, str(data.email))


@app.post("/auth/reset-password")
def reset(data: s.Reset, request: Request, db=Depends(db_session)):
    rate_limit(request, "reset", 5)
    identity.reset_password(db, data.token, data.password)
    return {"ok": True}


@app.post("/orders", status_code=201)
def checkout(data: s.Checkout, request: Request, user=Depends(principal), db=Depends(db_session)):
    rate_limit(request, "checkout", 15)
    key, access = request.headers.get("idempotency-key", ""), request.headers.get("x-order-token", "")
    try:
        UUID(key)
    except ValueError:
        raise Problem("A valid checkout key is required.")
    if not 43 <= len(access) <= 100:
        raise Problem("A secure order access token is required.")
    return ordering.create_order(db, data, key, access, user)


@app.get("/orders")
def list_orders(user=Depends(require()), db=Depends(db_session)):
    return ordering.list_orders(db, user)


@app.get("/orders/{reference}")
def get_order(reference: str, request: Request, user=Depends(principal), db=Depends(db_session)):
    order = ordering.authorized_order(db, reference, user, request.headers.get("x-order-token"))
    return ordering.snapshot(db, order, bool(user and user.role == "kitchen"))


@app.post("/orders/{reference}/handoff")
def handoff(reference: str, request: Request, user=Depends(principal), db=Depends(db_session)):
    order = ordering.authorized_order(db, reference, user, request.headers.get("x-order-token"))
    return ordering.initiate_handoff(db, order)


@app.patch("/orders/{reference}/status")
def status(
    reference: str,
    data: s.StatusChange,
    user=Depends(require("admin", "operator", "kitchen")),
    db=Depends(db_session),
):
    return ordering.transition(db, reference, user, data.status, data.version)


@app.get("/events")
async def events(request: Request, reference: str | None = None):
    token = request.headers.get("x-order-token")
    cookie = request.cookies.get("oriade_session")

    # Authorization is rechecked on each snapshot, so revoked sessions cannot keep streaming.
    def read_snapshot():
        with SessionLocal() as db:
            user, _ = identity.authenticate(db, cookie)
            if reference:
                order = ordering.authorized_order(db, reference, user, token)
                return ordering.snapshot(db, order, bool(user and user.role == "kitchen"))
            if not user:
                raise Problem("Please sign in.", 401)
            return ordering.list_orders(db, user)

    initial = await asyncio.to_thread(read_snapshot)

    async def stream():
        previous = None
        current = initial
        for _ in range(120):
            if await request.is_disconnected():
                return
            payload = json.dumps(current, sort_keys=True)
            if payload != previous:
                yield f"event: snapshot\ndata: {payload}\n\n"
                previous = payload
            else:
                yield ": heartbeat\n\n"
            await asyncio.sleep(3)
            try:
                current = await asyncio.to_thread(read_snapshot)
            except Problem:
                yield "event: expired\ndata: {}\n\n"
                return

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})


@app.get("/addresses")
def addresses(user=Depends(require()), db=Depends(db_session)):
    return customers.addresses(db, user)


@app.post("/addresses", status_code=201)
def add_address(data: s.AddressInput, user=Depends(require()), db=Depends(db_session)):
    return customers.save_address(db, user, data)


@app.delete("/addresses/{address_id}")
def remove_address(address_id: UUID, user=Depends(require()), db=Depends(db_session)):
    return customers.delete_address(db, user, address_id)


@app.post("/admin/items", status_code=201)
def create_item(data: s.ItemInput, user=Depends(require("admin", "operator")), db=Depends(db_session)):
    return catalog.save_item(db, user, data)


@app.put("/admin/items/{item_id}")
def edit_item(
    item_id: UUID, data: s.ItemInput, user=Depends(require("admin", "operator")), db=Depends(db_session)
):
    return catalog.save_item(db, user, data, item_id)


@app.put("/admin/items/{item_id}/stock")
def edit_stock(
    item_id: UUID, data: s.StockInput, user=Depends(require("admin", "operator")), db=Depends(db_session)
):
    return operations.update_stock(db, user, item_id, data.remaining)


@app.post("/admin/categories", status_code=201)
def add_category(data: s.CategoryInput, user=Depends(require("admin", "operator")), db=Depends(db_session)):
    return operations.save_entity(db, user, Category, data)


@app.put("/admin/categories/{entity_id}")
def edit_category(
    entity_id: UUID, data: s.CategoryInput, user=Depends(require("admin", "operator")), db=Depends(db_session)
):
    return operations.save_entity(db, user, Category, data, entity_id)


@app.post("/admin/locations", status_code=201)
def add_location(data: s.LocationInput, user=Depends(require("admin")), db=Depends(db_session)):
    return operations.save_entity(db, user, Location, data)


@app.put("/admin/locations/{entity_id}")
def edit_location(
    entity_id: UUID, data: s.LocationInput, user=Depends(require("admin")), db=Depends(db_session)
):
    return operations.save_entity(db, user, Location, data, entity_id)


@app.post("/admin/zones", status_code=201)
def add_zone(data: s.ZoneInput, user=Depends(require("admin", "operator")), db=Depends(db_session)):
    return operations.save_entity(db, user, Zone, data)


@app.put("/admin/zones/{entity_id}")
def edit_zone(
    entity_id: UUID, data: s.ZoneInput, user=Depends(require("admin", "operator")), db=Depends(db_session)
):
    return operations.save_entity(db, user, Zone, data, entity_id)


@app.get("/admin/reports")
def get_reports(user=Depends(require("admin", "operator")), db=Depends(db_session)):
    return reports(db)


@app.get("/admin/users")
def get_users(user=Depends(require("admin")), db=Depends(db_session)):
    return [
        {**identity.public_user(u), "active": u.active}
        for u in db.scalars(select(User).order_by(User.created_at.desc()).limit(200))
    ]


@app.patch("/admin/users/{user_id}")
def edit_user(user_id: UUID, data: s.StaffInput, user=Depends(require("admin")), db=Depends(db_session)):
    return operations.update_staff(db, user, user_id, data)


@app.get("/admin/audit")
def get_audit(user=Depends(require("admin")), db=Depends(db_session)):
    return [
        {
            "id": str(a.id),
            "action": a.action,
            "target": a.target,
            "details": a.details,
            "created_at": a.created_at.isoformat(),
        }
        for a in db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(200))
    ]


@app.post("/admin/images")
def upload_image(file: UploadFile, user=Depends(require("admin", "operator"))):
    from oriade.modules.catalog.images import upload

    return upload(file)
