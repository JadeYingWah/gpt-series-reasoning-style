"""Fixed-window rate limiter."""
import time


class RateLimiter:
    def __init__(self, limit=3, window_seconds=60):
        self.limit = limit
        self.window = window_seconds
        self._hits = {}  # key -> (window_start, count)

    def allow(self, key="default"):
        now = time.time()
        start, count = self._hits.get(key, (None, 0))
        if start is None or now - start >= self.window:
            start, count = now, 0
        count += 1
        self._hits[key] = (start, count)
        return count <= self.limit
