"""Explicitly invoked schema migration Lambda.

This handler is not attached to API traffic. Operators invoke it during a
release so concurrent cold starts never race schema changes.
"""

from __future__ import annotations

from typing import Any

from davdeploy.db import run_migrations


def handler(_event: dict[str, Any], _context: Any) -> dict[str, str]:
    run_migrations()
    return {"status": "migrations-complete"}
