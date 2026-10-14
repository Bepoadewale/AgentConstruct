"""Bounded local API load smoke; never targets a non-local host by default."""

from __future__ import annotations

import argparse
import concurrent.futures
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/healthz")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("local_load_smoke only permits localhost targets")
    if not 1 <= args.requests <= 1_000 or not 1 <= args.concurrency <= 50:
        raise SystemExit("requests must be 1..1000 and concurrency must be 1..50")

    def request(_: int) -> float:
        started = time.perf_counter()
        with urlopen(Request(args.url, method="GET"), timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"unexpected HTTP status: {response.status}")
            response.read()
        return (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        latencies = list(pool.map(request, range(args.requests)))
    elapsed = time.perf_counter() - started
    latencies.sort()
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]
    print(
        f"local load smoke passed: requests={len(latencies)} concurrency={args.concurrency} "
        f"elapsed_seconds={elapsed:.3f} p95_ms={p95:.1f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
