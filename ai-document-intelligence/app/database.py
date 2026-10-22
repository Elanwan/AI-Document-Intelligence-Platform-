from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory: sessionmaker[Session] | None = None


def configure_database(database_url: str | None = None) -> None:
    global _engine, _session_factory
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    if url.startswith("sqlite:///./"):
        Path(url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)
    if _engine is not None:
        _engine.dispose()
    _engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def initialize_database() -> None:
    if _engine is None:
        configure_database()
    # Import registers model metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=_engine)


def get_db() -> Generator[Session, None, None]:
    if _session_factory is None:
        configure_database()
    assert _session_factory is not None
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()

