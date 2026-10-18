from __future__ import annotations

import pytest
from davdeploy import db


def test_hosted_mode_rejects_sqlite_database_url(monkeypatch):
    monkeypatch.delenv("DAVDEPLOY_DATABASE_SECRET_ARN", raising=False)
    monkeypatch.delenv("DAVDEPLOY_AURORA_CLUSTER_ARN", raising=False)
    monkeypatch.setenv("DAVDEPLOY_HOSTED_MODE", "true")
    monkeypatch.setenv("DAVDEPLOY_DATABASE_URL", "sqlite+pysqlite:////tmp/davdeploy.db")

    with pytest.raises(RuntimeError, match="durable PostgreSQL"):
        db.database_url()


def test_local_mode_keeps_sqlite_available(monkeypatch):
    monkeypatch.delenv("DAVDEPLOY_DATABASE_SECRET_ARN", raising=False)
    monkeypatch.delenv("DAVDEPLOY_AURORA_CLUSTER_ARN", raising=False)
    monkeypatch.setenv("DAVDEPLOY_HOSTED_MODE", "false")
    monkeypatch.setenv("DAVDEPLOY_DATABASE_URL", "sqlite+pysqlite:///./.local/test.db")

    assert db.database_url() == "sqlite+pysqlite:///./.local/test.db"


def test_database_url_uses_data_api_without_retrieving_database_password(monkeypatch):
    monkeypatch.setenv("DAVDEPLOY_AURORA_CLUSTER_ARN", "arn:aws:rds:us-east-1:123:cluster:db")
    monkeypatch.setenv("DAVDEPLOY_DATABASE_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:123:secret:db")
    monkeypatch.setenv("DAVDEPLOY_DATABASE_NAME", "davdeploy")

    assert db.database_url() == "postgresql+auroradataapi://:@/davdeploy"
