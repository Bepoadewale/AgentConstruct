from __future__ import annotations

import time

from davdeploy.db import SessionLocal, run_migrations
from davdeploy.service import ProductService
from davdeploy.telemetry import configure_tracing


def main() -> None:
    run_migrations()
    configure_tracing()
    while True:
        db = SessionLocal()
        try:
            service = ProductService(db)
            # All queues are durable. Cloud execution is separately gated and
            # uses only the configured profile adapter.
            if not service.run_next_discovery_job() and not service.run_next_cloud_execution():
                service.run_next_job()
        finally:
            db.close()
        time.sleep(0.25)


if __name__ == "__main__":
    main()
