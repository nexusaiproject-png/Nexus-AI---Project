from __future__ import annotations

import os
from collections import OrderedDict
from threading import Lock
from typing import Any, Callable


class TTLCache:
    def __init__(self, ttl_seconds: float = 30.0, max_items: int = 256) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        import time
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            expires, value = item
            if expires <= time.monotonic():
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        import time
        with self._lock:
            self._items[key] = (time.monotonic() + self.ttl_seconds, value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_items:
                self._items.popitem(last=False)


class BackgroundQueue:
    def __init__(self) -> None:
        self._jobs: list[Callable[[], Any]] = []
        self._lock = Lock()

    def enqueue(self, job: Callable[[], Any]) -> None:
        with self._lock:
            self._jobs.append(job)

    def drain(self, limit: int = 100) -> int:
        with self._lock:
            jobs = self._jobs[:limit]
            del self._jobs[:limit]
        for job in jobs:
            job()
        return len(jobs)


CACHE = TTLCache()
QUEUE = BackgroundQueue()


def worker_count() -> int:
    return max(1, int(os.getenv("NEXUS_WORKERS", "1")))
