"""Bounded SQS-triggered worker entry point.

SQS is the wake-up and retry transport. Durable workflow state and idempotency
remain in the control-plane database.
"""

from __future__ import annotations

import json
from typing import Any

from davdeploy.db import SessionLocal
from davdeploy.service import ProductService


def handler(event: dict[str, Any], _context: Any) -> dict[str, int]:
    records = event.get("Records") or [{}]
    processed = 0
    for record in records:
        with SessionLocal() as db:
            service = ProductService(db)
            body = record.get("body") if isinstance(record, dict) else None
            event = json.loads(body) if isinstance(body, str) else {}
            build_id = ((event.get("detail") or {}).get("build-id")) if isinstance(event, dict) else None
            if build_id and service.reconcile_cloud_execution_build(str(build_id)):
                processed += 1
                continue
            if (
                service.run_next_discovery_job()
                or service.run_next_cloud_execution()
                or service.run_next_job()
            ):
                processed += 1
    return {"records": len(records), "processed": processed}
