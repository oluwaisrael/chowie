import secrets
from fastapi import Depends, Request
from redis import Redis
from redis.exceptions import RedisError
from oriade.shared.db import db_session
from oriade.shared.config import settings
from oriade.shared.errors import Problem
from oriade.modules.identity.service import authenticate, digest

redis = Redis.from_url(settings().redis_url, decode_responses=True)


def rate_limit(request: Request, bucket: str, maximum=30):
    # Proxy headers are intentionally ignored. Configure trusted proxy addresses at deployment.
    identity = request.client.host if request.client else "unknown"
    key = f"rate:{bucket}:{digest(identity)}"
    try:
        count = redis.eval(
            "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n",
            1,
            key,
        )
    except RedisError:
        raise Problem("This service is temporarily unavailable. Please try again.", 503)
    if count > maximum:
        raise Problem("Too many requests. Please try again in a minute.", 429)


def principal(request: Request, db=Depends(db_session)):
    user, session = authenticate(db, request.cookies.get("oriade_session"))
    if session and request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf):
            raise Problem("Your session needs refreshing. Please reload the page.", 403)
    return user


def require(*roles):
    def dependency(user=Depends(principal)):
        if not user:
            raise Problem("Please sign in to continue.", 401)
        if roles and user.role not in roles:
            raise Problem("You do not have permission to perform this action.", 403)
        return user

    return dependency
