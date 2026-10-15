"""Small, dependency-free local rate-limit seam.

Disabled unless explicitly configured. Hosted deployments can replace it with a
shared edge/store without changing route code.
"""

from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = monotonic()
        hits = self._hits[key]
        while hits and hits[0] <= now - self.window_seconds:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True
