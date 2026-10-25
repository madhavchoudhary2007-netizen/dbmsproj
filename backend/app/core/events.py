import asyncio
import threading
from contextlib import suppress
from typing import Any
from uuid import UUID


class EventBus:
    def __init__(self) -> None:
        self.clients: dict[
            str, set[tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]]
        ] = {}
        self.lock = threading.RLock()

    def subscribe(self, sid: str | UUID) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=50)
        loop = asyncio.get_running_loop()
        with self.lock:
            self.clients.setdefault(str(sid), set()).add((loop, q))
        return q

    def unsubscribe(self, sid: str | UUID, q: asyncio.Queue[dict[str, Any]]) -> None:
        with self.lock:
            clients = self.clients.get(str(sid), set())
            clients.difference_update(item for item in list(clients) if item[1] is q)

    @staticmethod
    def _enqueue(q: asyncio.Queue[dict[str, Any]], event: dict[str, Any]) -> None:
        if q.full():
            with suppress(asyncio.QueueEmpty):
                q.get_nowait()
        with suppress(asyncio.QueueFull):
            q.put_nowait(event)

    def send(self, sid: str | UUID, event: dict[str, Any]) -> None:
        try:
            current = asyncio.get_running_loop()
        except RuntimeError:
            current = None
        with self.lock:
            subscribers = list(self.clients.get(str(sid), set()))
        for loop, q in subscribers:
            if loop is current:
                self._enqueue(q, event)
            else:
                loop.call_soon_threadsafe(self._enqueue, q, event)
