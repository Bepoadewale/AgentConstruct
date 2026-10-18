from __future__ import annotations

import pytest
from agentconstruct import db


def test_hosted_mode_rejects_sqlite_database_url(monkeypatch):
    monkeypatch.delenv("AGENTCONSTRUCT_DATABASE_SECRET_ARN", raising=False)
    monkeypatch.delenv("AGENTCONSTRUCT_AURORA_CLUSTER_ARN", raising=False)
    monkeypatch.setenv("AGENTCONSTRUCT_HOSTED_MODE", "true")
    monkeypatch.setenv("AGENTCONSTRUCT_DATABASE_URL", "sqlite+pysqlite:////tmp/agentconstruct.db")

    with pytest.raises(RuntimeError, match="durable PostgreSQL"):
        db.database_url()


def test_local_mode_keeps_sqlite_available(monkeypatch):
    monkeypatch.delenv("AGENTCONSTRUCT_DATABASE_SECRET_ARN", raising=False)
    monkeypatch.delenv("AGENTCONSTRUCT_AURORA_CLUSTER_ARN", raising=False)
    monkeypatch.setenv("AGENTCONSTRUCT_HOSTED_MODE", "false")
    monkeypatch.setenv("AGENTCONSTRUCT_DATABASE_URL", "sqlite+pysqlite:///./.local/test.db")

    assert db.database_url() == "sqlite+pysqlite:///./.local/test.db"


def test_database_url_uses_data_api_without_retrieving_database_password(monkeypatch):
    monkeypatch.setenv("AGENTCONSTRUCT_AURORA_CLUSTER_ARN", "arn:aws:rds:us-east-1:123:cluster:db")
    monkeypatch.setenv("AGENTCONSTRUCT_DATABASE_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:123:secret:db")
    monkeypatch.setenv("AGENTCONSTRUCT_DATABASE_NAME", "agentconstruct")

    assert db.database_url() == "postgresql+auroradataapi://:@/agentconstruct"
