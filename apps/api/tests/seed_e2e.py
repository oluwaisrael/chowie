"""Run only against a disposable database ending in _e2e."""
from sqlalchemy import select
from oriade.shared.db import SessionLocal, engine
from oriade.shared.models import User
from oriade.modules.identity.service import hasher
from oriade.cli import seed

if not engine.url.database.endswith('_e2e'):
    raise SystemExit('Use a dedicated database ending in _e2e')
seed()
with SessionLocal() as db:
    for role in ['admin','operator','kitchen']:
        email=f'{role}@e2e.example.com'
        if not db.scalar(select(User).where(User.email==email)):
            db.add(User(name=f'QA {role}',email=email,role=role,password_hash=hasher.hash('e2e-only-password-123')))
    db.commit()
