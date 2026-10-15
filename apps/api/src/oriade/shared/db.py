from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from oriade.shared.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings().database_url, pool_pre_ping=True, pool_size=10, max_overflow=10)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def db_session():
    with SessionLocal() as db:
        yield db
