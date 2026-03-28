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

from pathlib import Path

from aiohttp import web

from kai import events

log = logging.getLogger(__name__)

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
    # fall back to embedded HTML
    html_path = Path(__file__).parent.parent.parent / "workspace" / ".claude" / "dashboard.html"
    if html_path.exists():
        return web.Response(text=html_path.read_text(), content_type="text/html")
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")


async def _handle_history(request: web.Request) -> web.Response:
    since = request.query.get("since", "")
    all_events = events.recent(1000)
    if since:
        all_events = [e for e in all_events if e["ts"] > since]
    return web.json_response(all_events)


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


async def start(port: int = 3456) -> None:
    """Start the dashboard server on the given port."""
    global _runner
    app = web.Application()
    app.router.add_get("/", _handle_index)
    app.router.add_get("/events", _handle_events)
    app.router.add_get("/history", _handle_history)
    _runner = web.AppRunner(app, access_log=None)
    await _runner.setup()
    site = web.TCPSite(_runner, "127.0.0.1", port)
    await site.start()
    log.info("Dashboard server listening on http://localhost:%d", port)


async def stop() -> None:
    """Stop the dashboard server."""
    global _runner
    if _runner:
        await _runner.cleanup()
        _runner = None
