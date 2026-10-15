from celery import Celery
from sqlalchemy import select
from redis import Redis
from oriade.shared.config import settings
from oriade.shared.db import SessionLocal
from oriade.shared.models import Outbox, Notification, now

celery = Celery("oriade", broker=settings().redis_url)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={"publish-outbox": {"task": "oriade.publish_outbox", "schedule": 2.0}},
    broker_connection_retry_on_startup=True,
)


@celery.task(name="oriade.publish_outbox", autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def publish_outbox():
    redis = Redis.from_url(settings().redis_url)
    with SessionLocal() as db:
        events = db.scalars(
            select(Outbox)
            .where(Outbox.published_at.is_(None))
            .order_by(Outbox.created_at)
            .limit(100)
            .with_for_update(skip_locked=True)
        ).all()
        for event in events:
            # Shared wake-up hint only. Clients always recover authoritative state from PostgreSQL.
            redis.publish("oriade:orders", str(event.id))
            if not db.scalar(select(Notification).where(Notification.event_id == event.id)):
                db.add(Notification(event_id=event.id, kind=event.topic))
            event.published_at = now()
        db.commit()
    return len(events)
