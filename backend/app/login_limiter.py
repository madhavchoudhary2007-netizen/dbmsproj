"""In-memory, per-router login attempt windows."""

import math
import threading
import time
from collections import deque


class LoginLimiter:
    """Atomically limit attempts by account and trusted client address."""

    def __init__(self, limit: int = 5, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._accounts: dict[str, deque[float]] = {}
        self._sources: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _expire(self, counters: dict[str, deque[float]], cutoff: float) -> None:
        for key, attempts in tuple(counters.items()):
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if not attempts:
                del counters[key]

    def admit(self, account: str, source: str) -> int | None:
        """Record an admitted attempt or return seconds until capacity frees."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - self.window_seconds
            self._expire(self._accounts, cutoff)
            self._expire(self._sources, cutoff)
            account_attempts = self._accounts.get(account, ())
            source_attempts = self._sources.get(source, ())
            retry_at = now
            limited = False
            for attempts in (account_attempts, source_attempts):
                if len(attempts) >= self.limit:
                    limited = True
                    retry_at = max(retry_at, attempts[0] + self.window_seconds)
            if limited:
                return max(1, math.ceil(retry_at - now))
            self._accounts.setdefault(account, deque()).append(now)
            self._sources.setdefault(source, deque()).append(now)
            return None
