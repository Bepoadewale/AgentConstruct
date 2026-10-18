"""Bounded SQS-triggered worker entry point.

SQS is the wake-up and retry transport. Durable workflow state and idempotency
remain in the control-plane database.
"""

from __future__ import annotations

from typing import Any

from agentconstruct.db import SessionLocal
from agentconstruct.service import ProductService


def handler(event: dict[str, Any], _context: Any) -> dict[str, int]:
    records = event.get("Records") or [{}]
    processed = 0
    for _record in records:
        with SessionLocal() as db:
            service = ProductService(db)
            if (
                service.run_next_discovery_job()
                or service.run_next_cloud_execution()
                or service.run_next_job()
            ):
                processed += 1
    return {"records": len(records), "processed": processed}
