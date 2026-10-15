import hashlib
import secrets
from datetime import timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from sqlalchemy import select, delete
from oriade.shared.models import User, Session, PasswordReset, now
from oriade.shared.errors import Problem
from oriade.shared.config import settings

hasher = PasswordHasher()
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(24))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def public_user(user):
    return {"id": str(user.id), "name": user.name, "email": user.email, "role": user.role}


def register(db, name, email, password):
    email = email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise Problem("An account with this email already exists.", 409)
    user = User(name=name, email=email, password_hash=hasher.hash(password))
    db.add(user)
    db.commit()
    return user


def login(db, email, password):
    user = db.scalar(select(User).where(User.email == email.lower()))
    try:
        hasher.verify(user.password_hash if user else DUMMY_HASH, password)
    except (VerifyMismatchError, InvalidHashError):
        raise Problem("Email or password is incorrect.", 401)
    if not user or not user.active:
        raise Problem("Email or password is incorrect.", 401)
    token = secrets.token_urlsafe(32)
    session = Session(
        user_id=user.id,
        token_hash=digest(token),
        csrf=secrets.token_urlsafe(32),
        expires_at=now() + timedelta(days=settings().session_days),
    )
    db.add(session)
    db.commit()
    return user, session, token


def authenticate(db, token):
    if not token:
        return None, None
    session = db.scalar(
        select(Session).where(Session.token_hash == digest(token), Session.expires_at > now())
    )
    user = db.get(User, session.user_id) if session else None
    if not user or not user.active:
        return None, None
    return user, session


def reset_password(db, token, password):
    reset = db.scalar(
        select(PasswordReset).where(PasswordReset.token_hash == digest(token)).with_for_update()
    )
    if not reset or reset.used or reset.expires_at <= now():
        raise Problem("This reset link has expired or was already used.")
    user = db.get(User, reset.user_id)
    user.password_hash = hasher.hash(password)
    reset.used = True
    db.execute(delete(Session).where(Session.user_id == user.id))
    db.commit()


def logout(db, token):
    db.execute(delete(Session).where(Session.token_hash == digest(token)))
    db.commit()


def request_reset(db, email):
    from oriade.modules.notifications.email import send_reset

    if not settings().smtp_host:
        raise Problem("Password reset email is not configured. Please contact the restaurant.", 503)
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user:
        token = secrets.token_urlsafe(32)
        db.add(
            PasswordReset(user_id=user.id, token_hash=digest(token), expires_at=now() + timedelta(minutes=30))
        )
        db.commit()
        try:
            send_reset(user.email, token)
        except Exception:
            # Delivery failures must not reveal account existence or sensitive tokens.
            __import__("logging").getLogger("oriade").error("Password reset email delivery failed")
    return {"message": "If an account exists, a reset link will be emailed to you."}
