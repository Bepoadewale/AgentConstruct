"""Minimal local diagnostic for self-hosted operators."""

from __future__ import annotations

from agentconstruct.db import database_url, make_engine


def main() -> None:
    engine = make_engine()
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")
    print("AgentConstruct diagnostics: database reachable")
    print(f"Database dialect: {engine.dialect.name}")
    print(f"Database target configured: {'postgresql' if database_url().startswith('postgresql') else 'sqlite-local'}")


if __name__ == "__main__":
    main()
