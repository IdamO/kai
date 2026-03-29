"""
Live dashboard server for watching Kai's Claude subprocess in real-time.

Serves a single-page HTML dashboard on a separate port (default 3456) that
shows tool calls, text generation, and system events via Server-Sent Events.

Routes:
    GET /           — Dashboard HTML page
    GET /events     — SSE stream of Claude events
    GET /history    — JSON array of recent events (for initial page load)
"""

import asyncio
import json
import logging
import os
import re
import subprocess

from datetime import datetime, UTC
from pathlib import Path

import aiohttp
from aiohttp import web

from kai import events

log = logging.getLogger(__name__)

WORKSPACE = Path(__file__).parent.parent.parent / "workspace"
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "8080"))


def _webhook_secret() -> str:
    """Read at call time so dotenv has loaded."""
    return os.environ.get("WEBHOOK_SECRET", "")

_runner: web.AppRunner | None = None

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kai Live</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: #0d1117; color: #c9d1d9; font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', 'Menlo', monospace;
    font-size: 13px; line-height: 1.6;
}
#header {
    position: sticky; top: 0; z-index: 10;
    background: #161b22; border-bottom: 1px solid #30363d;
    padding: 10px 20px; display: flex; align-items: center; gap: 12px;
}
#header h1 { font-size: 13px; font-weight: 600; color: #58a6ff; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.idle { background: #3fb950; }
.dot.active { background: #d29922; animation: pulse 1s infinite; }
.dot.disconnected { background: #484f58; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
#stats { color: #484f58; font-size: 11px; margin-left: auto; }
#controls button {
    background: transparent; border: 1px solid #30363d; color: #8b949e; padding: 3px 10px;
    border-radius: 4px; cursor: pointer; font-size: 11px; font-family: inherit;
}
#controls button:hover { border-color: #58a6ff; color: #58a6ff; }
#feed { padding: 4px 0; }
.line { padding: 1px 20px; display: flex; gap: 0; white-space: pre-wrap; word-break: break-word; }
.line:hover { background: #161b22; }
.line .ts { color: #484f58; min-width: 70px; flex-shrink: 0; user-select: none; }
.line .label { min-width: 58px; flex-shrink: 0; font-weight: 600; user-select: none; }
.line .body { flex: 1; }
.line.think .label { color: #bc8cff; }
.line.think .body { color: #9d86c9; font-style: italic; }
.line.tool .label { color: #d29922; }
.line.tool .body { color: #e3b341; }
.line.tool .args { color: #6e7681; }
.line.text .label { color: #58a6ff; }
.line.text .body { color: #c9d1d9; }
.line.result .label { color: #a371f7; }
.line.result .body { color: #8b949e; }
.line.res .label { color: #3fb950; }
.line.res .body { color: #56d364; max-height: 150px; overflow-y: auto; }
.line.res.err .label { color: #f85149; }
.line.res.err .body { color: #ffa198; }
.line.system .label { color: #484f58; }
.line.system .body { color: #484f58; }
.line.sep { border-top: 1px solid #21262d; margin: 4px 0; padding: 0; height: 0; }
.collapsed .body { display: none; }
.line .toggle { color: #484f58; cursor: pointer; margin-left: 6px; font-size: 11px; user-select: none; }
.line .toggle:hover { color: #8b949e; }
#error { color: #f85149; padding: 20px; text-align: center; display: none; }
</style>
</head>
<body>
<div id="header">
    <h1>Kai Live</h1>
    <span class="dot disconnected" id="dot"></span>
    <span id="stats"></span>
    <div id="controls">
        <button onclick="clearFeed()">Clear</button>
    </div>
</div>
<div id="error"></div>
<div id="feed"></div>
<script>
const feed = document.getElementById('feed');
const dot = document.getElementById('dot');
const statsEl = document.getElementById('stats');
const errorEl = document.getElementById('error');
let count = 0, tools = 0, lastAct = 0;
function clearFeed() { feed.innerHTML = ''; count = 0; tools = 0; updateStats(); }
function updateStats() { statsEl.textContent = count + ' events / ' + tools + ' tools'; }
function setDot(s) { dot.className = 'dot ' + s; }

function ts(iso) {
    try { return new Date(iso).toLocaleTimeString('en-US', {hour12:false, hour:'2-digit', minute:'2-digit', second:'2-digit'}); }
    catch(e) { return '??:??:??'; }
}

function esc(s) { let d = document.createElement('span'); d.textContent = s; return d.innerHTML; }

function trunc(s, n) { return s && s.length > n ? s.slice(0, n) + '...' : (s || ''); }

function fmtInput(input) {
    if (!input || typeof input !== 'object') return String(input || '');
    // For common tools, show compact form
    if (input.command) return input.command;
    if (input.query) return input.query;
    if (input.url) return input.url + (input.prompt ? ' | ' + input.prompt : '');
    if (input.file_path) return input.file_path;
    if (input.pattern) return input.pattern + (input.path ? ' in ' + input.path : '');
    try { return JSON.stringify(input, null, 2); }
    catch(e) { return String(input); }
}

function addEvent(ev) {
    count++;
    let d = ev.data || {};
    let line = document.createElement('div');
    line.className = 'line';
    let time = '<span class="ts">' + ts(ev.ts) + ' </span>';

    if (ev.type === 'thinking') {
        line.className = 'line think';
        line.innerHTML = time + '<span class="label">THINK </span><span class="body">' + esc(d.thinking || '') + '</span>';
        setDot('active'); lastAct = Date.now();

    } else if (ev.type === 'tool_use') {
        tools++;
        line.className = 'line tool';
        let args = fmtInput(d.input);
        line.innerHTML = time + '<span class="label">TOOL  </span><span class="body">'
            + esc(d.tool || '?') + ' <span class="args">' + esc(args) + '</span></span>';
        setDot('active'); lastAct = Date.now();

    } else if (ev.type === 'tool_result') {
        line.className = 'line res' + (d.is_error ? ' err' : '');
        line.innerHTML = time + '<span class="label">' + (d.is_error ? 'ERR   ' : 'RES   ') + '</span>'
            + '<span class="body">' + esc(d.output || '') + '</span>';

    } else if (ev.type === 'text') {
        line.className = 'line text';
        line.innerHTML = time + '<span class="label">TEXT  </span><span class="body">' + esc(d.text || '') + '</span>';
        setDot('active'); lastAct = Date.now();

    } else if (ev.type === 'result') {
        line.className = 'line result';
        let dur = d.duration_ms ? (d.duration_ms/1000).toFixed(1) + 's' : '';
        let cost = d.cost ? '$' + d.cost.toFixed(4) : '';
        let status = d.is_error ? 'ERROR' : 'DONE';
        line.innerHTML = time + '<span class="label">DONE  </span><span class="body">'
            + esc(status + ' ' + dur + ' ' + cost) + '</span>';
        setDot('idle');
        // Add separator before each completed interaction (newest on top)
        let sep = document.createElement('div');
        sep.className = 'line sep';
        feed.prepend(line);
        feed.prepend(sep);
        updateStats();
        return;

    } else if (ev.type === 'mid_stream') {
        line.className = 'line text';
        line.style.borderLeft = '3px solid #f0883e';
        line.innerHTML = time + '<span class="label" style="color:#f0883e">MSG&gt;&gt; </span><span class="body">' + esc(d.text || '') + '</span>';
        setDot('active'); lastAct = Date.now();

    } else if (ev.type === 'raw') {
        let rtype = d.type || 'raw';
        if (rtype === 'user' && d.preview) {
            let p = d.preview || '';
            if (p.includes('tool_result')) {
                line.className = 'line res';
                let m = p.match(/"text":\s*"([\s\S]*?)(?:"\s*[,}])/);
                let out = m ? m[1].replace(/\\n/g, '\n').replace(/\\t/g, '\t') : '(result received)';
                line.innerHTML = time + '<span class="label">RES   </span><span class="body">' + esc(out) + '</span>';
            } else {
                return;
            }
        } else if (rtype === 'rate_limit_event') {
            return;
        } else {
            line.className = 'line system';
            line.innerHTML = time + '<span class="label">SYS   </span><span class="body">' + esc(rtype) + '</span>';
        }

    } else if (ev.type === 'system') {
        line.className = 'line system';
        let sid = (d.session_id || '').slice(0, 8);
        line.innerHTML = time + '<span class="label">SYS   </span><span class="body">session ' + esc(sid) + '</span>';

    } else {
        line.className = 'line system';
        line.innerHTML = time + '<span class="label">???   </span><span class="body">' + esc(ev.type + ': ' + JSON.stringify(d)) + '</span>';
    }

    feed.prepend(line);
    updateStats();
    while (feed.children.length > 2000) feed.removeChild(feed.lastChild);
}

// Track latest timestamp to only fetch new events
let lastTs = '';
let polling = false;

function loadEvents() {
    let url = '/history' + (lastTs ? '?since=' + encodeURIComponent(lastTs) : '');
    fetch(url)
        .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(evts => {
            errorEl.style.display = 'none';
            if (!polling) setDot('idle');
            if (evts.length > 0) {
                evts.forEach(addEvent);
                lastTs = evts[evts.length - 1].ts;
            }
            polling = true;
        })
        .catch(e => {
            if (!polling) {
                errorEl.textContent = 'Failed to load: ' + e.message;
                errorEl.style.display = 'block';
            }
            setDot('disconnected');
        });
}

// Initial load
loadEvents();

// Poll every 1.5 seconds for new events
setInterval(loadEvents, 1500);

// Auto-detect idle
setInterval(() => {
    if (lastAct && Date.now() - lastAct > 10000 && dot.className.includes('active')) setDot('idle');
}, 3000);
</script>
</body>
</html>"""


async def _handle_index(request: web.Request) -> web.Response:
    # Serve from file if it exists (allows hot-reload without restart),
    # fall back to embedded HTML.  Check workspace root first (avoids
    # .claude/ sensitive-dir permission issues), then .claude/, then embedded.
    for rel in ("dashboard.html", ".claude/dashboard.html"):
        html_path = WORKSPACE / rel
        if html_path.exists():
            return web.Response(text=html_path.read_text(), content_type="text/html")
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")


async def _handle_history(request: web.Request) -> web.Response:
    since_ts = request.query.get("since", "")
    before = request.query.get("before", "")
    limit = min(int(request.query.get("limit", "500")), 1000)
    if since_ts:
        # Catch-up / gap-fill — read from disk (survives buffer rollover)
        result = events.since(since_ts, before=before, limit=limit)
        resp = web.json_response(result)
    elif before:
        # Paginating older events — read from disk
        resp = web.json_response(events.paginate(before=before, limit=limit))
    else:
        # Initial load — disk first, memory fallback
        result = events.paginate(before="", limit=limit)
        if not result:
            result = events.recent(limit)
        resp = web.json_response(result)
    resp.headers["Cache-Control"] = "no-store"
    return resp


async def _handle_events(request: web.Request) -> web.StreamResponse:
    """SSE endpoint — streams events in real-time."""
    resp = web.StreamResponse()
    resp.content_type = "text/event-stream"
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"
    await resp.prepare(request)

    q = events.subscribe()
    try:
        while True:
            try:
                ev = await asyncio.wait_for(q.get(), timeout=30)
                data = json.dumps(ev)
                await resp.write(f"data: {data}\n\n".encode())
            except TimeoutError:
                # Send keepalive comment to prevent proxy/browser timeout
                await resp.write(b": keepalive\n\n")
            except ConnectionResetError:
                break
    finally:
        events.unsubscribe(q)
    return resp


async def _handle_tasks(request: web.Request) -> web.Response:
    """Parse TASKS.md into structured JSON."""
    tasks_path = WORKSPACE / ".memory" / "TASKS.md"
    if not tasks_path.exists():
        return web.json_response({"focus": [], "dynamic": [], "raw": ""})
    raw = tasks_path.read_text()

    # Parse focus section
    focus = []
    in_focus = False
    for line in raw.split("\n"):
        if "## Current Focus" in line:
            in_focus = True
            continue
        if line.startswith("## ") and in_focus:
            break
        if in_focus and line.strip().startswith("**"):
            m = re.match(r"\*\*(.+?)\*\*:?\s*(.*)", line.strip())
            if m:
                focus.append({"name": m.group(1), "detail": m.group(2)})

    # Parse dynamic tasks
    dynamic = []
    in_dynamic = False
    for line in raw.split("\n"):
        if "## Dynamic Tasks" in line:
            in_dynamic = True
            continue
        if line.startswith("## ") and in_dynamic:
            break
        if in_dynamic and line.strip().startswith("- ["):
            m = re.match(r"- \[(.)\]\s*\*\*(.+?)\*\*\s*[—–-]\s*(.*)", line.strip())
            if m:
                status = {"x": "done", "~": "running", " ": "pending"}.get(m.group(1), "pending")
                dynamic.append({"status": status, "name": m.group(2), "detail": m.group(3)})

    return web.json_response({"focus": focus, "dynamic": dynamic})


async def _handle_daily_log(request: web.Request) -> web.Response:
    """Return today's daily log entries as structured JSON."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = WORKSPACE / ".memory" / "logs" / f"{today}.md"
    if not log_path.exists():
        return web.json_response({"date": today, "entries": []})
    raw = log_path.read_text()
    entries = []
    for m in re.finditer(r"## (\d{2}:\d{2})\s*\[(\w+)\]\s*\n(.*?)(?=\n## |\Z)", raw, re.DOTALL):
        entries.append({
            "time": m.group(1),
            "category": m.group(2),
            "text": m.group(3).strip()[:500],
        })
    return web.json_response({"date": today, "entries": entries})


async def _handle_processes(request: web.Request) -> web.Response:
    """Return running monitored processes."""
    # Read TASKS.md for PID references
    tasks_path = WORKSPACE / ".memory" / "TASKS.md"
    pids = {}
    if tasks_path.exists():
        raw = tasks_path.read_text()
        for m in re.finditer(r"PID (\d+)", raw):
            pid = int(m.group(1))
            # Get context around the PID mention
            start = max(0, m.start() - 80)
            end = min(len(raw), m.end() + 80)
            ctx = raw[start:end].replace("\n", " ").strip()
            pids[pid] = ctx

    # Check which PIDs are alive
    processes = []
    for pid, ctx in pids.items():
        try:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "pid,pcpu,pmem,etime,rss,command"],
                capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and len(result.stdout.strip().split("\n")) > 1:
                line = result.stdout.strip().split("\n")[1].strip()
                parts = line.split(None, 5)
                processes.append({
                    "pid": pid,
                    "cpu": parts[1] if len(parts) > 1 else "?",
                    "mem": parts[2] if len(parts) > 2 else "?",
                    "elapsed": parts[3] if len(parts) > 3 else "?",
                    "rss_kb": int(parts[4]) if len(parts) > 4 else 0,
                    "command": parts[5][:100] if len(parts) > 5 else "?",
                    "context": ctx,
                    "alive": True,
                })
            else:
                processes.append({"pid": pid, "context": ctx, "alive": False})
        except Exception:
            processes.append({"pid": pid, "context": ctx, "alive": False})

    return web.json_response(processes)


async def _handle_jobs_proxy(request: web.Request) -> web.Response:
    """Proxy to the webhook server's job API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://localhost:{WEBHOOK_PORT}/api/jobs",
                headers={"X-Webhook-Secret": _webhook_secret()},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                data = await resp.json()
                return web.json_response(data)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=502)


async def _handle_action_items(request: web.Request) -> web.Response:
    """Extract action items that need user input from TASKS.md."""
    tasks_path = WORKSPACE / ".memory" / "TASKS.md"
    items = []
    if tasks_path.exists():
        raw = tasks_path.read_text()
        for line in raw.split("\n"):
            line = line.strip()
            # Look for unchecked items with keywords suggesting user action needed
            if line.startswith("- [ ]") and any(kw in line.upper() for kw in
                    ["NEEDS", "BLOCKED", "OVERDUE", "NEEDS IDAM", "WAITING"]):
                m = re.match(r"- \[ \]\s*\*\*(.+?)\*\*\s*[—–-]\s*(.*)", line)
                if m:
                    items.append({"name": m.group(1), "detail": m.group(2), "urgent": "OVERDUE" in line.upper()})
    return web.json_response(items)


async def _handle_system_health(request: web.Request) -> web.Response:
    """System health: uptime, memory, disk, Claude subprocess status."""
    info = {}
    project_root = Path(__file__).parent.parent.parent
    try:
        # Kai process uptime
        kai_pid = None
        pid_file = project_root / "kai.pid"
        if pid_file.exists():
            kai_pid = int(pid_file.read_text().strip())
        if kai_pid:
            result = subprocess.run(
                ["ps", "-p", str(kai_pid), "-o", "etime,rss,pcpu"],
                capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    parts = lines[1].split()
                    info["kai_uptime"] = parts[0] if parts else "?"
                    info["kai_rss_kb"] = int(parts[1]) if len(parts) > 1 else 0
                    info["kai_cpu"] = parts[2] if len(parts) > 2 else "?"
            info["kai_pid"] = kai_pid

        # Claude subprocess - find it via process tree
        claude_result = subprocess.run(
            ["pgrep", "-f", "claude.*stream-json"],
            capture_output=True, text=True, timeout=5)
        if claude_result.returncode == 0 and claude_result.stdout.strip():
            claude_pid = int(claude_result.stdout.strip().split("\n")[0])
            info["claude_pid"] = claude_pid
            ps_result = subprocess.run(
                ["ps", "-p", str(claude_pid), "-o", "etime,rss,pcpu"],
                capture_output=True, text=True, timeout=5)
            if ps_result.returncode == 0:
                lines = ps_result.stdout.strip().split("\n")
                if len(lines) > 1:
                    parts = lines[1].split()
                    info["claude_uptime"] = parts[0] if parts else "?"
                    info["claude_rss_kb"] = int(parts[1]) if len(parts) > 1 else 0

        # Is Claude actively responding?
        responding_file = project_root / ".responding_to"
        info["claude_responding"] = responding_file.exists()
        if responding_file.exists():
            try:
                info["responding_to"] = responding_file.read_text().strip()[:100]
            except Exception:
                pass

        # Disk usage
        result = subprocess.run(["df", "-h", str(WORKSPACE)],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                parts = lines[1].split()
                info["disk_total"] = parts[1] if len(parts) > 1 else "?"
                info["disk_used"] = parts[2] if len(parts) > 2 else "?"
                info["disk_avail"] = parts[3] if len(parts) > 3 else "?"
                info["disk_pct"] = parts[4] if len(parts) > 4 else "?"

        # Recent session cost from last log line
        log_file = project_root / "logs" / "kai.log"
        if log_file.exists():
            tail = subprocess.run(
                ["tail", "-100", str(log_file)],
                capture_output=True, text=True, timeout=5)
            if tail.returncode == 0:
                for line in reversed(tail.stdout.split("\n")):
                    if "cost=$" in line:
                        cost_m = re.search(r"cost=\$([\d.]+)", line)
                        dur_m = re.search(r"duration=(\d+)ms", line)
                        if cost_m:
                            info["last_cost"] = float(cost_m.group(1))
                        if dur_m:
                            info["last_duration_s"] = int(dur_m.group(1)) // 1000
                        break

    except Exception:
        pass

    info["timestamp"] = datetime.now(UTC).isoformat()
    return web.json_response(info)


async def _handle_status(request: web.Request) -> web.Response:
    """Aggregated status: health + current focus + action items + recent activity."""
    # Gather all status data in parallel
    health_resp = await _handle_system_health(request)
    health = json.loads(health_resp.body)

    tasks_resp = await _handle_tasks(request)
    tasks = json.loads(tasks_resp.body)

    # Recent events summary
    all_events = events.recent(100)
    last_event_ts = all_events[-1]["ts"] if all_events else None
    tool_count = sum(1 for e in all_events if e.get("type") in ("tool_use", "tool"))
    text_count = sum(1 for e in all_events if e.get("type") == "text")

    # Action items needing user attention
    action_items = []
    tasks_path = WORKSPACE / ".memory" / "TASKS.md"
    if tasks_path.exists():
        raw = tasks_path.read_text()
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]") and any(kw in line.upper() for kw in
                    ["NEEDS", "BLOCKED", "OVERDUE", "NEEDS IDAM", "WAITING"]):
                m = re.match(r"- \[ \]\s*\*\*(.+?)\*\*\s*[-]+\s*(.*)", line)
                if m:
                    action_items.append({"name": m.group(1), "detail": m.group(2),
                                         "urgent": "OVERDUE" in line.upper()})

    # Pending (non-done) task count
    pending = [t for t in (tasks.get("dynamic") or [])
               if isinstance(t, dict) and t.get("status") != "done"]
    running = [t for t in (tasks.get("dynamic") or [])
               if isinstance(t, dict) and t.get("status") == "running"]

    status = {
        "health": health,
        "focus": tasks.get("focus", []),
        "pending_tasks": len(pending),
        "running_tasks": len(running),
        "action_items": action_items,
        "recent_events": {
            "total": len(all_events),
            "tools": tool_count,
            "text": text_count,
            "last_ts": last_event_ts,
        },
    }
    return web.json_response(status)


async def _handle_send_message(request: web.Request) -> web.Response:
    """Send a message to Kai via the webhook server."""
    try:
        body = await request.json()
        text = body.get("text", "")
        if not text:
            return web.json_response({"error": "No text"}, status=400)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://localhost:{WEBHOOK_PORT}/api/send-message",
                headers={
                    "X-Webhook-Secret": _webhook_secret(),
                    "Content-Type": "application/json",
                },
                json={"text": text},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                return web.json_response(data)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=502)


async def _handle_conversations(request: web.Request) -> web.Response:
    """Search/browse conversation history from .claude/history/ JSONL files."""
    q = request.query.get("q", "").lower()
    date = request.query.get("date", "")
    limit = min(int(request.query.get("limit", "100")), 500)
    offset = int(request.query.get("offset", "0"))

    history_dir = WORKSPACE / ".claude" / "history"
    if not history_dir.exists():
        return web.json_response({"messages": [], "total": 0, "dates": []})

    files = sorted(history_dir.glob("*.jsonl"), reverse=True)
    dates = [f.stem for f in files]

    if date:
        files = [f for f in files if date in f.name]

    messages = []
    for f in files:
        try:
            for line in f.read_text().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    text = msg.get("text") or ""
                    if q and q not in text.lower():
                        continue
                    messages.append({
                        "ts": msg.get("ts", ""),
                        "dir": msg.get("dir", ""),
                        "text": text[:1000],
                        "date": f.stem,
                        "has_media": bool(msg.get("media")),
                    })
                except json.JSONDecodeError:
                    continue
        except Exception:
            continue

    total = len(messages)
    messages = messages[offset:offset + limit]
    return web.json_response({"messages": messages, "total": total, "dates": dates})


async def _handle_ingestors(request: web.Request) -> web.Response:
    """Parse ingestor stats from TASKS.md."""
    tasks_path = WORKSPACE / ".memory" / "TASKS.md"
    if not tasks_path.exists():
        return web.json_response([])
    raw = tasks_path.read_text()

    ingestors = []
    # Match lines like "- NTS: **COMPLETE** — 767K tracks, 728K transitions"
    # or "- [~] **Mixcloud API** — RUNNING (PID 5002)..."
    for m in re.finditer(
        r"- (?:\[.\]\s*)?\*?\*?(\w[\w\s]*?\w)\*?\*?\s*(?::|—)\s*\*?\*?(\w+)\*?\*?\s*[—–-]\s*(.*?)(?=\n|$)",
        raw,
    ):
        name = m.group(1).strip().rstrip("*").lstrip("*")
        status_raw = m.group(2).strip()
        detail = m.group(3).strip()[:300]

        # Extract numbers
        tracks = ""
        transitions = ""
        for nm in re.finditer(r"([\d,.]+[KMB]?)\s*tracks", detail):
            tracks = nm.group(1)
        for nm in re.finditer(r"([\d,.]+[KMB]?)\s*transitions", detail):
            transitions = nm.group(1)
        pid_m = re.search(r"PID (\d+)", detail)

        ingestors.append({
            "name": name,
            "status": status_raw.upper(),
            "detail": detail,
            "tracks": tracks,
            "transitions": transitions,
            "pid": int(pid_m.group(1)) if pid_m else None,
        })

    return web.json_response(ingestors)


async def _handle_pipeline(request: web.Request) -> web.Response:
    """Return pipeline progress summary parsed from TASKS.md and processes."""
    tasks_path = WORKSPACE / ".memory" / "TASKS.md"
    pipeline = {
        "als": {"status": "unknown", "progress": 0, "detail": ""},
        "mert": {"status": "unknown", "progress": 0, "detail": ""},
        "ingestors": {"running": 0, "complete": 0, "total_transitions": ""},
        "models": [],
    }
    if not tasks_path.exists():
        return web.json_response(pipeline)
    raw = tasks_path.read_text()

    # ALS progress
    als_m = re.search(r"ALS.*?iteration\s*(\d+)/(\d+)\s*\((\d+)%\)", raw)
    if als_m:
        pipeline["als"] = {
            "status": "training",
            "progress": int(als_m.group(3)),
            "iteration": f"{als_m.group(1)}/{als_m.group(2)}",
            "detail": "Phase 2 training",
        }

    # MERT status
    if "UNBLOCKED" in raw and "Modal MERT" in raw:
        pipeline["mert"] = {"status": "ready", "progress": 0, "detail": "Modal A100 authenticated, waiting for ALS"}

    # Model results
    for m in re.finditer(r"MODEL-(\d+).*?:\s*\*\*(.*?)\*\*", raw):
        pipeline["models"].append({"id": f"MODEL-{m.group(1)}", "result": m.group(2)})

    # Ingestor counts
    running = len(re.findall(r"\[~\].*?ingest|RUNNING.*?PID", raw, re.IGNORECASE))
    complete = len(re.findall(r"COMPLETE", raw))
    total_m = re.search(r"Total curated transitions:\s*\*?\*?~?([\d.]+[KMB]\+?)", raw)
    pipeline["ingestors"] = {
        "running": running,
        "complete": complete,
        "total_transitions": total_m.group(1) if total_m else "",
    }

    return web.json_response(pipeline)


async def _handle_log_dates(request: web.Request) -> web.Response:
    """List available daily log dates."""
    log_dir = WORKSPACE / ".memory" / "logs"
    if not log_dir.exists():
        return web.json_response([])
    dates = sorted([f.stem for f in log_dir.glob("*.md")], reverse=True)
    return web.json_response(dates)


async def _handle_daily_log_date(request: web.Request) -> web.Response:
    """Return daily log entries for a specific date."""
    date = request.match_info.get("date", datetime.now().strftime("%Y-%m-%d"))
    log_path = WORKSPACE / ".memory" / "logs" / f"{date}.md"
    if not log_path.exists():
        return web.json_response({"date": date, "entries": []})
    raw = log_path.read_text()
    entries = []
    for m in re.finditer(r"## (\d{2}:\d{2})\s*\[(\w+)\]\s*\n(.*?)(?=\n## |\Z)", raw, re.DOTALL):
        entries.append({
            "time": m.group(1),
            "category": m.group(2),
            "text": m.group(3).strip()[:500],
        })
    return web.json_response({"date": date, "entries": entries})


async def _handle_todos(request: web.Request) -> web.Response:
    """Return the most recent non-empty TodoWrite state from ~/.claude/todos/."""
    todos_dir = Path.home() / ".claude" / "todos"
    if not todos_dir.exists():
        return web.json_response({"todos": [], "source": None})
    # Find the most recently modified non-empty JSON file
    best = None
    best_mtime = 0
    for f in todos_dir.glob("*.json"):
        if f.stat().st_size > 5:  # skip empty []
            mt = f.stat().st_mtime
            if mt > best_mtime:
                best_mtime = mt
                best = f
    if not best:
        return web.json_response({"todos": [], "source": None})
    try:
        data = json.loads(best.read_text())
        # Filter to only in_progress and pending items
        active = [t for t in data if t.get("status") != "completed"]
        return web.json_response({"todos": data, "active": active, "source": best.name})
    except Exception:
        return web.json_response({"todos": [], "source": None})


async def _handle_files_list(request: web.Request) -> web.Response:
    """List directory contents within the workspace."""
    rel_path = request.query.get("path", ".")
    target = (WORKSPACE / rel_path).resolve()

    # Confine to workspace
    try:
        target.relative_to(WORKSPACE.resolve())
    except ValueError:
        return web.json_response({"error": "Path outside workspace"}, status=403)

    if not target.exists():
        return web.json_response({"error": "Not found"}, status=404)

    if not target.is_dir():
        return web.json_response({"error": "Not a directory"}, status=400)

    entries = []
    try:
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            name = item.name
            # Skip hidden dirs that aren't .memory or .claude
            if name.startswith(".") and name not in (".memory", ".claude"):
                continue
            try:
                stat = item.stat()
                entries.append({
                    "name": name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                    "ext": item.suffix.lower() if item.is_file() else None,
                })
            except OSError:
                continue
    except PermissionError:
        return web.json_response({"error": "Permission denied"}, status=403)

    # Include breadcrumb path relative to workspace
    try:
        rel = str(target.relative_to(WORKSPACE.resolve()))
    except ValueError:
        rel = "."

    return web.json_response({"path": rel, "entries": entries})


async def _handle_file_read(request: web.Request) -> web.Response:
    """Read a file's contents from the workspace."""
    rel_path = request.query.get("path", "")
    if not rel_path:
        return web.json_response({"error": "Missing path"}, status=400)

    target = (WORKSPACE / rel_path).resolve()

    # Confine to workspace
    try:
        target.relative_to(WORKSPACE.resolve())
    except ValueError:
        return web.json_response({"error": "Path outside workspace"}, status=403)

    if not target.exists():
        return web.json_response({"error": "Not found"}, status=404)

    if not target.is_file():
        return web.json_response({"error": "Not a file"}, status=400)

    # Size limit: 500KB
    if target.stat().st_size > 512_000:
        return web.json_response({"error": "File too large (>500KB)"}, status=413)

    # Text file extensions we'll serve
    text_exts = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".js",
                 ".ts", ".sh", ".css", ".html", ".csv", ".log", ".env", ".cfg",
                 ".ini", ".xml", ".jsonl", ""}
    if target.suffix.lower() not in text_exts:
        return web.json_response({"error": f"Binary file type: {target.suffix}"}, status=415)

    try:
        content = target.read_text(errors="replace")
    except Exception:
        return web.json_response({"error": "Could not read file"}, status=500)

    return web.json_response({
        "path": rel_path,
        "name": target.name,
        "content": content,
        "size": len(content),
    })


async def _handle_static(request: web.Request) -> web.Response:
    """Serve static files from workspace/.claude/static/."""
    filename = request.match_info.get("filename", "")
    static_dir = WORKSPACE / ".claude" / "static"
    filepath = static_dir / filename
    if not filepath.exists() or not filepath.is_file():
        return web.Response(status=404, text="Not found")
    content_types = {
        ".css": "text/css", ".js": "application/javascript",
        ".png": "image/png", ".svg": "image/svg+xml",
        ".ico": "image/x-icon", ".woff2": "font/woff2",
    }
    ct = content_types.get(filepath.suffix, "application/octet-stream")
    return web.Response(body=filepath.read_bytes(), content_type=ct)


async def start(port: int = 3456) -> None:
    """Start the dashboard server on the given port."""
    global _runner
    app = web.Application()
    # Frontend
    app.router.add_get("/", _handle_index)
    app.router.add_get("/events", _handle_events)
    app.router.add_get("/history", _handle_history)
    app.router.add_get("/static/{filename:.+}", _handle_static)
    # Mission Control API
    app.router.add_get("/api/tasks", _handle_tasks)
    app.router.add_get("/api/log", _handle_daily_log)
    app.router.add_get("/api/processes", _handle_processes)
    app.router.add_get("/api/jobs", _handle_jobs_proxy)
    app.router.add_get("/api/action-items", _handle_action_items)
    app.router.add_get("/api/health", _handle_system_health)
    app.router.add_get("/api/status", _handle_status)
    app.router.add_post("/api/message", _handle_send_message)
    app.router.add_get("/api/conversations", _handle_conversations)
    app.router.add_get("/api/ingestors", _handle_ingestors)
    app.router.add_get("/api/pipeline", _handle_pipeline)
    app.router.add_get("/api/log/dates", _handle_log_dates)
    app.router.add_get("/api/log/{date}", _handle_daily_log_date)
    app.router.add_get("/api/todos", _handle_todos)
    app.router.add_get("/api/files", _handle_files_list)
    app.router.add_get("/api/file", _handle_file_read)
    _runner = web.AppRunner(app, access_log=None)
    await _runner.setup()
    site = web.TCPSite(_runner, "0.0.0.0", port)
    await site.start()
    log.info("Mission Control listening on http://localhost:%d", port)


async def stop() -> None:
    """Stop the dashboard server."""
    global _runner
    if _runner:
        await _runner.cleanup()
        _runner = None
