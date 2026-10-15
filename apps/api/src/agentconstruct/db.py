from __future__ import annotations

import json
import os
from collections.abc import Generator
from pathlib import Path
from urllib.parse import quote

import boto3
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from agentconstruct.models import Base


def database_url() -> str:
    secret_arn = os.getenv("AGENTCONSTRUCT_DATABASE_SECRET_ARN")
    if secret_arn:
        payload = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
        secret = json.loads(str(payload["SecretString"]))
        username = quote(str(secret["username"]))
        password = quote(str(secret["password"]))
        host = str(secret["host"])
        port = str(secret.get("port", 5432))
        database = str(os.getenv("AGENTCONSTRUCT_DATABASE_NAME", secret.get("dbname", "agentconstruct")))
        return f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"
    resolved = os.getenv("AGENTCONSTRUCT_DATABASE_URL", "sqlite+pysqlite:///./.local/agentconstruct.db")
    if os.getenv("AGENTCONSTRUCT_HOSTED_MODE", "false").lower() == "true" and resolved.startswith(
        "sqlite"
    ):
        raise RuntimeError("hosted AgentConstruct runtime requires durable PostgreSQL; SQLite is not allowed")
    return resolved


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
        database = selected.url.database
        if database and database not in {":memory:"}:
            path = Path(database)
            if path.parent != Path("."):
                path.parent.mkdir(parents=True, exist_ok=True)
            elif str(path).startswith(".local/"):
                Path(".local").mkdir(exist_ok=True)
    with selected.begin() as connection:
        # API and worker can start together in Compose. PostgreSQL needs one
        # transaction-scoped lock before either process creates the migration table.
        if selected.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(84202601)"))
        connection.execute(
            text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
        )
        version = connection.execute(
            text("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")
        ).scalar_one()
        if version < 1:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (16)"))
            return
        if version < 2:
            connection.execute(
                text("ALTER TABLE execution_jobs ADD COLUMN environment_id VARCHAR(36)")
            )
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (2)"))
            version = 2
        if version < 3:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (3)"))
            version = 3
        if version < 4:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (4)"))
            version = 4
        if version < 5:
            columns = {column["name"] for column in inspect(connection).get_columns("cloud_connections")}
            additions = {
                "account_id": "ALTER TABLE cloud_connections ADD COLUMN account_id VARCHAR(12)",
                "discovery_role_arn": "ALTER TABLE cloud_connections ADD COLUMN discovery_role_arn TEXT",
                "external_id": "ALTER TABLE cloud_connections ADD COLUMN external_id TEXT",
                "setup_state": "ALTER TABLE cloud_connections ADD COLUMN setup_state VARCHAR(32) DEFAULT 'DRAFT'",
            }
            for name, statement in additions.items():
                if name not in columns:
                    connection.execute(text(statement))
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (5)"))
            version = 5
        if version < 6:
            columns = {column["name"] for column in inspect(connection).get_columns("cloud_connections")}
            if "external_id_secret_ref" not in columns:
                connection.execute(
                    text("ALTER TABLE cloud_connections ADD COLUMN external_id_secret_ref TEXT")
                )
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (6)"))
            version = 6
        if version < 7:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (7)"))
            version = 7
        if version < 8:
            columns = {column["name"] for column in inspect(connection).get_columns("repository_connections")}
            if "selected_branch" not in columns:
                connection.execute(
                    text("ALTER TABLE repository_connections ADD COLUMN selected_branch VARCHAR(255)")
                )
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (8)"))
            version = 8
        if version < 9:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (9)"))
            version = 9
        if version < 10:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (10)"))
            version = 10
        if version < 11:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (11)"))
            version = 11
        if version < 12:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (12)"))
            version = 12
        if version < 13:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (13)"))
            version = 13
        if version < 14:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (14)"))
            version = 14
        if version < 15:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (15)"))
            version = 15
        if version < 16:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (16)"))
            version = 16
        if version < 17:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (17)"))
            version = 17
        if version < 18:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (18)"))
            version = 18
        if version < 19:
            Base.metadata.create_all(bind=connection)
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (19)"))


def session() -> Generator[Session, None, None]:
    current = SessionLocal()
    try:
        yield current
    finally:
        current.close()
