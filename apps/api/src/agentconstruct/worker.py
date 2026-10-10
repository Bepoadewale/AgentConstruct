from __future__ import annotations

import time

from agentconstruct.db import SessionLocal, run_migrations
from agentconstruct.service import ProductService
from agentconstruct.telemetry import configure_tracing


def main() -> None:
    run_migrations()
    configure_tracing()
    while True:
        db = SessionLocal()
        try:
            service = ProductService(db)
            # Both queues are durable. Discovery is deliberately read-only.
            if not service.run_next_discovery_job():
                service.run_next_job()
        finally:
            db.close()
        time.sleep(0.25)


if __name__ == "__main__":
    main()
