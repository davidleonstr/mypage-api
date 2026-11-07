import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Tiny in-memory sliding-window limiter.

    State is per process: with several gunicorn workers the effective limit is
    multiplied by the worker count. That is fine for stopping form spam and
    password guessing on a small site.
    """

    def __init__(self, limit: int, window_seconds: float):
        self.limit = limit
        self.window = window_seconds
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key, now):
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if not hits:
            self._hits.pop(key, None)
            return None
        return hits

    def is_limited(self, key) -> bool:
        with self._lock:
            hits = self._prune(key, time.monotonic())
            return bool(hits) and len(hits) >= self.limit

    def hit(self, key) -> bool:
        """Record one event. Returns False once the key is over the limit."""
        with self._lock:
            now = time.monotonic()
            if len(self._hits) > 10_000:
                for stale in list(self._hits):
                    self._prune(stale, now)
            self._prune(key, now)
            self._hits[key].append(now)
            return len(self._hits[key]) <= self.limit
