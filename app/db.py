"""Database engine/session setup.

SQLite for the MVP (a file under ./data), with DATABASE_URL externalized so
switching to Postgres later is a connection-string change, not a rewrite.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.DATABASE_URL
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        # sqlite:///./data/tenants.db -> ensure ./data exists before connecting.
        if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
            db_path = url[len("sqlite:///"):]
            if db_path and db_path != ":memory:":
                parent = Path(db_path).parent
                if str(parent) not in ("", "."):
                    parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, connect_args=connect_args)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import db_models  # noqa: F401 - import so models register on Base.metadata

    Base.metadata.create_all(bind=engine)
