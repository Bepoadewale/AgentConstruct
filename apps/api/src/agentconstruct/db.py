from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from agentconstruct.models import Base


def database_url() -> str:
    return os.getenv("AGENTCONSTRUCT_DATABASE_URL", "sqlite+pysqlite:///./.local/agentconstruct.db")


def make_engine(url: str | None = None) -> Engine:
    resolved = url or database_url()
    connect_args = {"check_same_thread": False} if resolved.startswith("sqlite") else {}
    return create_engine(resolved, future=True, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def run_migrations(target: Engine | None = None) -> None:
    """Small versioned bootstrap for V1; replace with an expanded migration set as schemas evolve."""
    selected = target or engine
    if str(selected.url).startswith("sqlite"):
        Path(".local").mkdir(exist_ok=True)
    with selected.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)"))
        version = connection.execute(text("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")).scalar_one()
        if version < 1:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (1)"))


def session() -> Generator[Session, None, None]:
    current = SessionLocal()
    try:
        yield current
    finally:
        current.close()
