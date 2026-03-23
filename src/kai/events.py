"""
In-memory event buffer for the live dashboard.

Provides a simple pub/sub system: claude.py pushes events as they arrive
from the Claude subprocess, and the dashboard SSE endpoint subscribes to
receive them in real-time.

Events are kept in a circular buffer (last 500) so the dashboard can show
recent history when first opened.
"""

import asyncio
from collections import deque
from datetime import datetime, UTC

_buffer: deque[dict] = deque(maxlen=2000)
_subscribers: list[asyncio.Queue] = []


def push(event_type: str, data: dict) -> None:
    """Push an event to the buffer and notify all subscribers."""
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "type": event_type,
        "data": data,
    }
    _buffer.append(entry)
    dead = []
    for q in _subscribers:
        try:
            q.put_nowait(entry)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.remove(q)


def recent(n: int = 200) -> list[dict]:
    """Return the last N events."""
    items = list(_buffer)
    return items[-n:]


def subscribe() -> asyncio.Queue:
    """Create a new subscriber queue for SSE streaming."""
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    """Remove a subscriber queue."""
    try:
        _subscribers.remove(q)
    except ValueError:
        pass
