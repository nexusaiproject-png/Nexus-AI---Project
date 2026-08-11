from __future__ import annotations

import json
import logging
import time
from collections import Counter, deque
from threading import Lock
from typing import Any

from fastapi import APIRouter, Response

router = APIRouter(prefix="/observability", tags=["observability"])

_logger = logging.getLogger("nexus.observability")
_events: deque[dict[str, Any]] = deque(maxlen=1000)
_counts: Counter[str] = Counter()
_lock = Lock()
_started = time.time()


def record_event(event: str, **fields: Any) -> None:
    payload = {"event": event, "timestamp": time.time(), **fields}
    with _lock:
        _events.append(payload)
        _counts[event] += 1
    _logger.info(json.dumps(payload, separators=(",", ":"), default=str))


@router.get("/metrics")
def metrics() -> Response:
    with _lock:
        counts = dict(_counts)
    lines = [f"nexus_uptime_seconds {time.time() - _started:.3f}"]
    for event, count in sorted(counts.items()):
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in event)
        lines.append(f'nexus_events_total{{event="{safe}"}} {count}')
    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


@router.get("/events")
def events(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    with _lock:
        items = list(_events)[-limit:]
    return {"events": items}


@router.get("/status")
def status() -> dict[str, Any]:
    with _lock:
        total = sum(_counts.values())
    return {"status": "ok", "uptime_seconds": round(time.time() - _started, 3), "events": total}
