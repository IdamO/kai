"""
In-memory event buffer with disk persistence for the live dashboard.

Events are kept in a circular buffer (last 10,000) for real-time SSE streaming,
and persisted to daily JSONL files for infinite scrollback history.
"""

import asyncio
import json
from collections import deque
from datetime import datetime, UTC
from pathlib import Path

_buffer: deque[dict] = deque(maxlen=10000)
_subscribers: list[asyncio.Queue] = []
_EVENTS_DIR = Path(__file__).parent.parent.parent / "workspace" / ".memory" / "events"


def push(event_type: str, data: dict) -> None:
    """Push an event to the buffer, notify subscribers, and persist to disk."""
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "type": event_type,
        "data": data,
    }
    _buffer.append(entry)
    _persist(entry)
    dead = []
    for q in _subscribers:
        try:
            q.put_nowait(entry)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.remove(q)


def _persist(entry: dict) -> None:
    """Append event to daily JSONL file on disk."""
    try:
        _EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        date = entry["ts"][:10]
        path = _EVENTS_DIR / f"{date}.jsonl"
        compact = entry
        # Truncate thinking text (ephemeral, huge, not useful in history)
        data = entry.get("data", {})
        if entry.get("type") == "thinking" and len(data.get("thinking", "")) > 1000:
            compact = {**entry, "data": {**data, "thinking": data["thinking"][:1000] + "..."}}
        with open(path, "a") as f:
            f.write(json.dumps(compact, separators=(",", ":")) + "\n")
    except Exception:
        pass  # Never let persistence failure break event flow


def recent(n: int = 200) -> list[dict]:
    """Return the last N events from in-memory buffer (chronological order)."""
    items = list(_buffer)
    return items[-n:]


def since(after: str, before: str = "", limit: int = 5000) -> list[dict]:
    """Return events after `after` timestamp (and optionally before `before`).

    Reads from disk JSONL files — more reliable than memory buffer for gap-filling.
    """
    if not _EVENTS_DIR.exists():
        return []
    results = []
    after_date = after[:10]
    before_date = before[:10] if before else "9999-99-99"
    files = sorted(_EVENTS_DIR.glob("*.jsonl"))
    files = [f for f in files if f.stem >= after_date and f.stem <= before_date]
    for f in files:
        try:
            lines = f.read_text().strip().split("\n")
        except Exception:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = ev.get("ts", "")
            if ts <= after:
                continue
            if before and ts >= before:
                continue
            results.append(ev)
            if len(results) >= limit:
                return results
    return results


def paginate(before: str = "", limit: int = 100) -> list[dict]:
    """Return up to `limit` events before `before` timestamp, in chronological order.

    Reads from daily JSONL files on disk. If `before` is empty, returns the
    latest events. Used for infinite scroll pagination.
    """
    if not _EVENTS_DIR.exists():
        return []
    results = []
    files = sorted(_EVENTS_DIR.glob("*.jsonl"), reverse=True)
    # Skip files entirely after the cursor date
    if before:
        before_date = before[:10]
        files = [f for f in files if f.stem <= before_date]
    for f in files:
        try:
            lines = f.read_text().strip().split("\n")
        except Exception:
            continue
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if before and ev.get("ts", "") >= before:
                continue
            results.append(ev)
            if len(results) >= limit:
                results.reverse()
                return results
    results.reverse()
    return results


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
