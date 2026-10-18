"""Fail-fast self-hosted configuration validation; never contacts a cloud provider."""

from __future__ import annotations

import os

from davdeploy.providers import ProviderConfiguration


def main() -> int:
    hosted = os.getenv("DAVDEPLOY_HOSTED_MODE", "false").lower() == "true"
    database_url = os.getenv("DAVDEPLOY_DATABASE_URL", "sqlite+pysqlite:///./.local/davdeploy.db")
    errors: list[str] = []
    if hosted and database_url.startswith("sqlite"):
        errors.append("hosted mode requires PostgreSQL, not SQLite")
    for name in (
        "DAVDEPLOY_JWKS_URL",
        "DAVDEPLOY_OIDC_ISSUER",
        "DAVDEPLOY_OIDC_AUDIENCE",
        "DAVDEPLOY_OPA_URL",
    ):
        if hosted and not os.getenv(name):
            errors.append(f"hosted mode requires {name}")
    for name in ("DAVDEPLOY_JWKS_URL", "DAVDEPLOY_OIDC_ISSUER", "DAVDEPLOY_OPA_URL"):
        value = os.getenv(name, "")
        if hosted and value and not value.startswith("https://"):
            errors.append(f"hosted mode requires an HTTPS {name}")
    if hosted and os.getenv("DAVDEPLOY_LOCAL_SIGNING_KEY"):
        errors.append("hosted mode must not use DAVDEPLOY_LOCAL_SIGNING_KEY")
    errors.extend(ProviderConfiguration.from_environment().validation_errors(hosted=hosted))
    if errors:
        print("Environment validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Environment validation passed. No cloud action was attempted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
