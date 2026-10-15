"""Fail-fast self-hosted configuration validation; never contacts a cloud provider."""

from __future__ import annotations

import os

from agentconstruct.providers import ProviderConfiguration


def main() -> int:
    hosted = os.getenv("AGENTCONSTRUCT_HOSTED_MODE", "false").lower() == "true"
    database_url = os.getenv("AGENTCONSTRUCT_DATABASE_URL", "sqlite+pysqlite:///./.local/agentconstruct.db")
    errors: list[str] = []
    if hosted and database_url.startswith("sqlite"):
        errors.append("hosted mode requires PostgreSQL, not SQLite")
    if hosted and not os.getenv("AGENTCONSTRUCT_JWKS_URL"):
        errors.append("hosted mode requires AGENTCONSTRUCT_JWKS_URL")
    if hosted and os.getenv("AGENTCONSTRUCT_LOCAL_SIGNING_KEY"):
        errors.append("hosted mode must not use AGENTCONSTRUCT_LOCAL_SIGNING_KEY")
    errors.extend(ProviderConfiguration.from_environment().validation_errors(hosted=hosted))
    if errors:
        print("Environment validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Environment validation passed. No cloud action was attempted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
