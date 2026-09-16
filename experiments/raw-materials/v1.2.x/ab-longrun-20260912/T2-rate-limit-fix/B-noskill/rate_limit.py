"""Fixed rate limiter: per-key fixed window."""
import time


class RateLimiter:
    def __init__(self, limit=3, window_seconds=60):
        self.limit = limit
        self.window = window_seconds
        # per-key: (window_start, count)
        self._state = {}

    def allow(self, key="default"):
        now = time.time()
        window_start, count = self._state.get(key, (now, 0))
        if now - window_start >= self.window:
            window_start, count = now, 0
        if count >= self.limit:
            self._state[key] = (window_start, count)
            return False
        self._state[key] = (window_start, count + 1)
        return True
