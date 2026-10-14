from __future__ import annotations

import pytest
from agentconstruct import db


def test_hosted_mode_rejects_sqlite_database_url(monkeypatch):
    monkeypatch.delenv("AGENTCONSTRUCT_DATABASE_SECRET_ARN", raising=False)
    monkeypatch.setenv("AGENTCONSTRUCT_HOSTED_MODE", "true")
    monkeypatch.setenv("AGENTCONSTRUCT_DATABASE_URL", "sqlite+pysqlite:////tmp/agentconstruct.db")

    with pytest.raises(RuntimeError, match="durable PostgreSQL"):
        db.database_url()


def test_local_mode_keeps_sqlite_available(monkeypatch):
    monkeypatch.delenv("AGENTCONSTRUCT_DATABASE_SECRET_ARN", raising=False)
    monkeypatch.setenv("AGENTCONSTRUCT_HOSTED_MODE", "false")
    monkeypatch.setenv("AGENTCONSTRUCT_DATABASE_URL", "sqlite+pysqlite:///./.local/test.db")

    assert db.database_url() == "sqlite+pysqlite:///./.local/test.db"


def test_database_url_can_be_built_from_secrets_manager_reference(monkeypatch):
    class FakeSecretsManager:
        def get_secret_value(self, SecretId):
            assert SecretId == "arn:aws:secretsmanager:us-east-1:123:secret:db"
            return {
                "SecretString": (
                    '{"username":"agentconstruct","password":"p@ss word",'
                    '"host":"db.internal","port":5432,"dbname":"ignored"}'
                )
            }

    class FakeBoto3:
        @staticmethod
        def client(service):
            assert service == "secretsmanager"
            return FakeSecretsManager()

    monkeypatch.setattr(db, "boto3", FakeBoto3)
    monkeypatch.setenv("AGENTCONSTRUCT_DATABASE_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:123:secret:db")
    monkeypatch.setenv("AGENTCONSTRUCT_DATABASE_NAME", "agentconstruct")

    assert db.database_url() == (
        "postgresql+psycopg://agentconstruct:p%40ss%20word@db.internal:5432/agentconstruct"
    )
