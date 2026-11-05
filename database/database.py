from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import ROOT_DIR, Settings
from database.models import Base


def _database_url(settings: Settings) -> str:
    url = settings.database_url
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        return f"sqlite:///{(ROOT_DIR / url.removeprefix('sqlite:///')).resolve()}"
    return url


def create_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    settings = settings or Settings.load()
    url = _database_url(settings)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(settings: Settings | None = None) -> Iterator[Session]:
    session = create_session_factory(settings)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
