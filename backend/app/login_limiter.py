"""In-memory, per-router login attempt windows."""

import math
import threading
import time
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class LoginAdmission:
    token: object | None
    retry_after: int | None = None


class LoginLimiter:
    """Atomically limit attempts by account and trusted client address."""

    def __init__(self, limit: int = 5, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._accounts: dict[str, deque[tuple[float, object]]] = {}
        self._sources: dict[str, deque[tuple[float, object]]] = {}
        self._lock = threading.Lock()

    def _expire(self, counters: dict[str, deque[tuple[float, object]]], cutoff: float) -> None:
        for key, attempts in tuple(counters.items()):
            while attempts and attempts[0][0] <= cutoff:
                attempts.popleft()
            if not attempts:
                del counters[key]

    def admit(self, account: str, source: str) -> LoginAdmission:
        """Reserve a slot, or return the wait needed to regain capacity."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - self.window_seconds
            self._expire(self._accounts, cutoff)
            self._expire(self._sources, cutoff)
            account_attempts = self._accounts.get(account, deque())
            source_attempts = self._sources.get(source, deque())
            retry_at = now
            limited = False
            for attempts in (account_attempts, source_attempts):
                if len(attempts) >= self.limit:
                    limited = True
                    retry_at = max(retry_at, attempts[0][0] + self.window_seconds)
            if limited:
                return LoginAdmission(None, max(1, math.ceil(retry_at - now)))
            token = object()
            self._accounts.setdefault(account, deque()).append((now, token))
            self._sources.setdefault(source, deque()).append((now, token))
            return LoginAdmission(token)

    def release(self, account: str, source: str, token: object) -> None:
        """Remove only this request's reservation from both limit windows."""
        with self._lock:
            for counters, key in ((self._accounts, account), (self._sources, source)):
                attempts = counters.get(key)
                if attempts is None:
                    continue
                counters[key] = deque(item for item in attempts if item[1] is not token)
                if not counters[key]:
                    del counters[key]
