"""
Persistent Claude Code subprocess manager.

Provides functionality to:
1. Manage a long-running Claude Code subprocess with stream-json I/O
2. Inject identity, memory, history, and API context on each new session
3. Stream partial responses for real-time Telegram message updates
4. Handle workspace switching, model changes, and graceful shutdown

This is the core bridge between Telegram (bot.py) and Claude Code. Instead of
launching a new Claude process per message, a single persistent process is kept
alive and communicated with via newline-delimited JSON on stdin/stdout. This
preserves Claude's conversation context across messages within a session.

The stream-json protocol:
    Input:  {"type": "user", "message": {"role": "user", "content": [...]}}
    Output: {"type": "system", ...}      — session metadata
            {"type": "assistant", ...}   — partial text (streaming)
            {"type": "result", ...}      — final response with cost/session info

Context injection on first message of each session:
    1. Identity (CLAUDE.md from home workspace, when in a foreign workspace)
    2. Personal memory (MEMORY.md from home workspace)
    3. Workspace memory (MEMORY.md from current workspace, if different from home)
    4. Recent conversation history (last 20 messages from JSONL logs)
    5. Scheduling API endpoint info (URL, secret, field reference)
"""

import asyncio
import json
import logging
import os
import signal
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from kai import events
from kai.history import get_recent_history

log = logging.getLogger(__name__)


# ── Protocol types ───────────────────────────────────────────────────


@dataclass
class ClaudeResponse:
    """
    Final response from a Claude Code interaction.

    Attributes:
        success: True if Claude returned a valid response, False on error.
        text: The full response text (accumulated from streaming chunks).
        session_id: Claude's session identifier (used for session continuity).
        cost_usd: Cost of this interaction in USD (from Claude's billing).
        duration_ms: Wall-clock duration of the interaction in milliseconds.
        error: Error message if success is False, None otherwise.
    """

    success: bool
    text: str
    session_id: str | None = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    error: str | None = None


@dataclass
class StreamEvent:
    """
    A partial update emitted during Claude's streaming response.

    Yielded by PersistentClaude.send() as Claude generates text. The final
    event has done=True and includes the complete ClaudeResponse.

    Attributes:
        text_so_far: Accumulated response text up to this point.
        done: True if this is the final event (response complete or error).
        response: The complete ClaudeResponse, set only when done=True.
    """

    text_so_far: str
    done: bool = False
    response: ClaudeResponse | None = None


# ── Persistent Claude process ────────────────────────────────────────


class PersistentClaude:
    """
    A long-running Claude Code subprocess using stream-json I/O for multi-turn chat.

    Manages the lifecycle of the Claude process: starting, sending messages,
    streaming responses, killing/restarting, and workspace switching. All message
    sends are serialized via an internal asyncio lock to prevent interleaving.

    The process runs with --permission-mode bypassPermissions (required for headless
    operation via Telegram) and --max-budget-usd to cap per-session spending.
    """

    # Proactive restart threshold: restart between messages when context
    # usage exceeds this fraction of the model's max window, preventing
    # compaction from ever firing mid-flight.
    CONTEXT_RESTART_RATIO = 0.65
    # Max context windows by model family (tokens)
    _MAX_CONTEXT = {"opus": 200_000, "sonnet": 200_000, "haiku": 200_000}
    # Periodic context refresh interval (inject TASKS + HACKS every N messages)
    REFRESH_INTERVAL = 15

    # Codex model mapping: empty string = use Codex default (works with ChatGPT subscription).
    # ChatGPT-auth Codex uses its own model set, not API models like gpt-4.1.
    _CODEX_MODELS: dict[str, str] = {}

    # Pin short model names to explicit model IDs so we control which version runs.
    # "sonnet" -> Sonnet 4.5 (not 4.6) per Idam's preference (2026-04-10).
    _MODEL_IDS: dict[str, str] = {
        "opus": "claude-opus-4-6",
        "sonnet": "claude-sonnet-4-5-20250929",
        "haiku": "claude-haiku-4-5-20251001",
    }

    def __init__(
        self,
        *,
        model: str = "opus",
        workspace: Path = Path("workspace"),
        home_workspace: Path | None = None,
        webhook_port: int = 8080,
        webhook_secret: str = "",
        max_budget_usd: float = 1.0,
        timeout_seconds: int = 120,
        services_info: list[dict] | None = None,
        claude_user: str | None = None,
        backend: str = "claude",  # "claude" or "codex"
    ):
        self.model = model
        self.workspace = workspace
        self.home_workspace = home_workspace or workspace
        self.webhook_port = webhook_port
        self.webhook_secret = webhook_secret
        self.max_budget_usd = max_budget_usd
        self.timeout_seconds = timeout_seconds
        self.services_info = services_info or []
        self.claude_user = claude_user
        self.backend = backend
        self._proc: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()  # Serializes all message sends
        self._session_id: str | None = None
        self._fresh_session = True  # True until the first message is sent
        self._stderr_task: asyncio.Task | None = None  # Background stderr drain
        self._message_count: int = 0
        self._last_pushed_session_id: str | None = None  # For A3: suppress duplicate system events
        self._last_input_tokens: int = 0  # For B4: track context usage
        self._needs_restart: bool = False  # For B4: flag for between-message restart
        self._compacted_mid_stream: bool = False  # For B2: mid-stream compaction detection

    def _build_context_injection(self) -> list[str]:
        """
        Build the full context injection payload.

        Returns a list of context blocks (MEMORY.md, TASKS.md, HACKS.md, etc.)
        that get prepended to a prompt. Called on fresh sessions and after
        compaction recovery — both need the same full context set.
        """
        from datetime import date

        parts: list[str] = []
        global_claude = Path.home() / ".claude"

        if self.workspace != self.home_workspace:
            identity_path = self.home_workspace / ".claude" / "CLAUDE.md"
            if identity_path.exists():
                identity = identity_path.read_text().strip()
                if identity:
                    parts.append(f"[Your core identity and instructions:]\n{identity}")

        user_id_path = global_claude / "user-identity.md"
        if user_id_path.exists():
            user_id = user_id_path.read_text().strip()
            if user_id:
                parts.append(f"[User identity — update this as you learn more about the user:]\n{user_id}")

        debt_path = global_claude / "behavioral-debt.yaml"
        if debt_path.exists():
            debt = debt_path.read_text().strip()
            if debt:
                parts.append(f"[Behavioral corrections — these override all other instructions:]\n{debt}")

        memory_path = self.home_workspace / ".claude" / "MEMORY.md"
        if memory_path.exists():
            memory = memory_path.read_text().strip()
            if memory:
                parts.append(f"[Your persistent memory from home workspace:]\n{memory}")

        memory_dir = self.home_workspace / ".memory"

        tasks_path = memory_dir / "TASKS.md"
        if tasks_path.exists():
            tasks = tasks_path.read_text().strip()
            if tasks:
                parts.append(f"[Current tasks and work state — update this as you work:]\n{tasks}")

        hacks_path = self.home_workspace / ".claude" / "HACKS.md"
        if hacks_path.exists():
            hacks = hacks_path.read_text().strip()
            if hacks:
                parts.append(f"[Proven workarounds and dead ends — check before multi-step operations:]\n{hacks}")

        ops_path = self.home_workspace / ".claude" / "personal-ops.md"
        if ops_path.exists():
            ops = ops_path.read_text().strip()
            if ops:
                parts.append(f"[Personal deadlines and operations:]\n{ops}")

        log_path = memory_dir / "logs" / f"{date.today().isoformat()}.md"
        if log_path.exists():
            log_content = log_path.read_text().strip()
            if log_content:
                lines = log_content.split("\n")
                recent_log = "\n".join(lines[-50:])
                parts.append(f"[Today's operational log (append to this as you work):]\n{recent_log}")

        if self.workspace != self.home_workspace:
            ws_memory_path = self.workspace / ".claude" / "MEMORY.md"
            if ws_memory_path.exists():
                ws_memory = ws_memory_path.read_text().strip()
                if ws_memory:
                    parts.append(f"[Your memory for this workspace ({self.workspace.name}):]\n{ws_memory}")

        recent = get_recent_history()
        if recent:
            parts.append(f"[Recent conversations (search .claude/history/ for full logs):]\n{recent}")

        if self.webhook_secret:
            api_note = (
                f"[Scheduling API: To create jobs, POST JSON to "
                f"http://localhost:{self.webhook_port}/api/schedule "
                f"with header 'X-Webhook-Secret: $KAI_WEBHOOK_SECRET' (environment variable). "
                f"Required fields: name, prompt, schedule_type, schedule_data. "
                f"Optional: job_type (reminder|claude), auto_remove (bool). "
                f"To list jobs: GET /api/jobs. To update: PATCH /api/jobs/{{id}}. "
                f"To delete: DELETE /api/jobs/{{id}}.]"
            )
            if self.workspace != self.home_workspace:
                api_note = (
                    f"[Workspace context: You are working in {self.workspace}. "
                    f"Your home workspace is {self.home_workspace}.]\n{api_note}"
                )
            parts.append(api_note)

        if self.webhook_secret:
            parts.append(
                f"[File API: To send a file to the user, POST JSON to "
                f"http://localhost:{self.webhook_port}/api/send-file "
                f"with header 'X-Webhook-Secret: $KAI_WEBHOOK_SECRET' (environment variable). "
                f'Required: "path" (absolute file path within the current workspace {self.workspace}). '
                f'Optional: "caption". Images are sent as photos, '
                f"everything else as documents.\n"
                f"Incoming files from the user are auto-saved to "
                f"{self.workspace}/files/ and their paths are included "
                f"in the message.]"
            )

        if self.services_info and self.webhook_secret:
            svc_lines = [
                "[External Services: To call external APIs, POST JSON to "
                f"http://localhost:{self.webhook_port}/api/services/{{name}} "
                f"with header 'X-Webhook-Secret: $KAI_WEBHOOK_SECRET' (environment variable). "
                "Request JSON fields (all optional): "
                '"body" (dict - forwarded as JSON), '
                '"params" (dict - query parameters), '
                '"path_suffix" (str - appended to base URL).',
                "",
                "Available services:",
            ]
            for svc in self.services_info:
                svc_lines.append(f"  - {svc['name']} ({svc['method']}): {svc['description']}")
                if svc.get("notes"):
                    svc_lines.append(f"    Notes: {svc['notes']}")
            svc_lines.append("")
            svc_lines.append(
                "Example (Perplexity web search):\n"
                f"  curl -s -X POST http://localhost:{self.webhook_port}/api/services/perplexity "
                f"-H 'Content-Type: application/json' "
                f"""-H "X-Webhook-Secret: $KAI_WEBHOOK_SECRET" """
                """-d '{"body": {"model": "sonar", "messages": [{"role": "user", "content": "your query"}]}}'"""
            )
            svc_lines.append(
                "Prefer external services over built-in WebSearch/WebFetch when available "
                "— they provide better results.]"
            )
            parts.append("\n".join(svc_lines))

        return parts

    @staticmethod
    def _extract_tasks_focus(tasks_text: str) -> str:
        """Extract the 'Current Focus' block from TASKS.md."""
        focus_start = tasks_text.find("## Current Focus")
        if focus_start < 0:
            return ""
        focus_end = tasks_text.find("\n## ", focus_start + 1)
        if focus_end > 0:
            return tasks_text[focus_start:focus_end].strip()
        return tasks_text[focus_start:focus_start + 500].strip()

    @staticmethod
    def _prepend_to_prompt(prompt: str | list, prefix: str) -> str | list:
        """Prepend a text block to a prompt (str or content-block list)."""
        if isinstance(prompt, str):
            return prefix + prompt
        return [{"type": "text", "text": prefix}] + prompt

    @property
    def is_alive(self) -> bool:
        """True if the Claude subprocess is running and hasn't exited."""
        return self._proc is not None and self._proc.returncode is None

    @property
    def session_id(self) -> str | None:
        """The current Claude session ID, or None if no session is active."""
        return self._session_id

    async def _ensure_started(self) -> None:
        """
        Start the Claude Code subprocess if not already running.

        Launches claude with stream-json I/O, bypassPermissions mode (required
        for headless operation), and the configured model and budget. The process
        runs in the current workspace directory and persists across messages.

        When claude_user is set, the process is spawned via sudo -u to run as
        a different OS user. The subprocess is started in its own process group
        (start_new_session=True) so the entire tree (sudo + claude) can be
        killed reliably via os.killpg().

        The stdout buffer limit is raised to 1 MiB (from the default 64 KiB)
        because large tool results from Claude can exceed the default.
        """
        if self.is_alive:
            return

        env = os.environ.copy()
        if self.webhook_secret:
            env["KAI_WEBHOOK_SECRET"] = self.webhook_secret

        if self.backend == "codex":
            # ── Codex backend: one-shot exec per message (no persistent session) ──
            # Codex doesn't support persistent stdin/stdout sessions like Claude.
            # We handle this by spawning a new `codex exec` per send() call.
            # _ensure_started() for codex is a no-op — the process is spawned
            # in _send_codex_locked() instead.
            log.info(
                "Codex backend configured (model=%s → %s)",
                self.model,
                self._CODEX_MODELS.get(self.model, self.model),
            )
            self._session_id = None
            self._fresh_session = True
            return

        # ── Claude backend (default): persistent subprocess ──
        claude_cmd = [
            "claude",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--verbose",
            "--model",
            self._MODEL_IDS.get(self.model, self.model),
            "--permission-mode",
            "bypassPermissions",
            "--effort",
            "max",
        ]

        # When running as a different user, spawn via sudo -u.
        # The subprocess runs with the target user's UID, home directory,
        # and environment - completely isolated from the bot user.
        if self.claude_user:
            cmd = ["sudo", "-u", self.claude_user, "--"] + claude_cmd
        else:
            cmd = claude_cmd

        resolved_model = self._MODEL_IDS.get(self.model, self.model)
        log.info(
            "Starting persistent Claude process (model=%s -> %s, user=%s)",
            self.model, resolved_model,
            self.claude_user or "(same as bot)",
        )

        # Remove API key so Claude Code uses the host's Max subscription
        # login instead of pay-per-use API billing.
        env.pop("ANTHROPIC_API_KEY", None)

        self._proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace),
            env=env,
            limit=4 * 1024 * 1024,  # 4 MiB; research tasks can produce very large JSON lines
            # When spawned via sudo, start in a new process group so we can
            # kill the entire tree (sudo + claude) via os.killpg(). Without
            # this, killing sudo may orphan the claude process.
            start_new_session=bool(self.claude_user),
        )
        self._session_id = None
        self._fresh_session = True

        # Drain stderr in background to prevent pipe buffer deadlock
        self._stderr_task = asyncio.create_task(self._drain_stderr())

    async def _drain_stderr(self) -> None:
        """
        Continuously read and discard stderr from the Claude process.

        Without this, the stderr pipe buffer fills up and the process deadlocks.
        Important lines (hooks, errors, warnings) are logged at INFO level.
        """
        while self._proc and self._proc.stderr:
            try:
                line = await self._proc.stderr.readline()
                if not line:
                    break
                text = line.decode().strip()
                if text:
                    # Elevate important stderr to INFO so we can see hooks and errors
                    lowered = text.lower()
                    if any(kw in lowered for kw in (
                        "hook", "error", "warning", "compac", "cost", "timeout",
                        "permission", "blocked", "fail", "reject",
                    )):
                        log.info("Claude stderr: %s", text[:500])
                    else:
                        log.debug("Claude stderr: %s", text[:200])
            except Exception:
                log.warning("Unexpected error in stderr drain", exc_info=True)
                break

    def _kill_proc(self, sig: int = signal.SIGKILL) -> None:
        """
        Send a signal to the Claude subprocess.

        When claude_user is set, the process runs in its own process group
        (via start_new_session=True). We must kill the entire group to
        ensure the actual claude process dies, not just the sudo wrapper.

        Args:
            sig: Signal to send. Defaults to SIGKILL.
        """
        if not self._proc or self._proc.returncode is not None:
            return
        try:
            if self.claude_user:
                os.killpg(os.getpgid(self._proc.pid), sig)
            else:
                self._proc.send_signal(sig)
        except OSError:
            # Catches ProcessLookupError, PermissionError, and any other
            # OS-level error from getpgid() or signal delivery
            pass

    async def send(self, prompt: str | list) -> AsyncIterator[StreamEvent]:
        """
        Send a message to Claude and yield streaming events.

        This is the main public interface. All sends are serialized via an
        internal lock so concurrent callers (e.g., a user message arriving
        while a cron job is running) queue rather than interleave.

        Args:
            prompt: Either a text string or a list of content blocks (for
                multi-modal messages like images).

        Yields:
            StreamEvent objects with accumulated text. The final event has
            done=True and includes the complete ClaudeResponse.
        """
        async with self._lock:
            async for event in self._send_locked(prompt):
                yield event

    async def _send_codex_locked(self, prompt: str | list) -> AsyncIterator[StreamEvent]:
        """
        Send a message to Codex and yield streaming events.

        Codex doesn't support persistent stdin/stdout sessions. Each call
        spawns a fresh `codex exec` process. Context injection is prepended
        to the prompt text as system-style instructions.
        """
        # Flatten content blocks to text for Codex
        if isinstance(prompt, list):
            text_parts = []
            for block in prompt:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block["text"])
                elif isinstance(block, str):
                    text_parts.append(block)
            prompt_text = "\n\n".join(text_parts)
        else:
            prompt_text = prompt

        # On first message, prepend context injection
        if self._fresh_session:
            self._fresh_session = False
            self._message_count = 0
            parts = self._build_context_injection()
            if parts:
                prompt_text = "\n\n".join(parts) + "\n\n" + prompt_text

        self._message_count += 1

        cmd = [
            "codex", "exec",
            "--json",
            "--dangerously-bypass-approvals-and-sandbox",
            "-C", str(self.workspace),
            prompt_text,
        ]
        # If a specific Codex model is mapped, pass it. Otherwise use Codex default
        # (which works with ChatGPT subscription auth — no API charges).
        codex_model = self._CODEX_MODELS.get(self.model)
        if codex_model:
            cmd.insert(-1, "-c")
            cmd.insert(-1, f'model="{codex_model}"')

        env = os.environ.copy()
        if self.webhook_secret:
            env["KAI_WEBHOOK_SECRET"] = self.webhook_secret

        log.info("Spawning Codex exec (model=%s, prompt_len=%d)", codex_model, len(prompt_text))

        try:
            self._proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace),
                env=env,
                limit=4 * 1024 * 1024,
            )
        except FileNotFoundError:
            yield StreamEvent(
                text_so_far="",
                done=True,
                response=ClaudeResponse(success=False, text="", error="codex CLI not found"),
            )
            return

        self._stderr_task = asyncio.create_task(self._drain_stderr())
        accumulated_text = ""

        try:
            while True:
                timeout = max(self.timeout_seconds * 5, 3600)
                try:
                    line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=timeout)
                except TimeoutError:
                    log.error("Codex silent for %ds — killing", timeout)
                    await self._kill()
                    yield StreamEvent(
                        text_so_far=accumulated_text, done=True,
                        response=ClaudeResponse(success=False, text=accumulated_text, error="Codex timed out"),
                    )
                    return

                if not line:
                    # Process finished
                    text = accumulated_text
                    yield StreamEvent(
                        text_so_far=text, done=True,
                        response=ClaudeResponse(
                            success=bool(text), text=text,
                            error=None if text else "Codex returned no output",
                        ),
                    )
                    return

                try:
                    event = json.loads(line.decode())
                except json.JSONDecodeError:
                    continue

                etype = event.get("type", "")

                # Map Codex JSONL events to our StreamEvent + dashboard events
                if etype == "thread.started":
                    sid = event.get("thread_id", "")
                    self._session_id = sid
                    events.push("system", {"session_id": sid, "backend": "codex"})

                elif etype == "item.completed":
                    item = event.get("item", {})
                    item_type = item.get("type", "")
                    if item_type == "agent_message":
                        new_text = item.get("text", "")
                        if new_text:
                            if accumulated_text and not accumulated_text.endswith("\n"):
                                accumulated_text += "\n\n"
                            accumulated_text += new_text
                            events.push("text", {"text": new_text})
                            yield StreamEvent(text_so_far=accumulated_text)
                    elif item_type == "command_execution":
                        events.push("tool_use", {
                            "tool": "shell",
                            "id": item.get("id", ""),
                            "input": {"command": item.get("command", "")},
                        })
                        output = item.get("aggregated_output", "")
                        if output:
                            events.push("tool_result", {
                                "id": item.get("id", ""),
                                "output": output[:500],
                                "is_error": item.get("exit_code", 0) != 0,
                            })

                elif etype == "turn.completed":
                    usage = event.get("usage", {})
                    events.push("result", {
                        "cost": 0,  # Codex doesn't report cost in JSONL
                        "duration_ms": 0,
                        "input_tokens": usage.get("input_tokens", 0),
                        "is_error": False,
                        "backend": "codex",
                    })

                elif etype == "turn.failed":
                    error_msg = str(event.get("error", "Codex turn failed"))
                    yield StreamEvent(
                        text_so_far=accumulated_text, done=True,
                        response=ClaudeResponse(success=False, text=accumulated_text, error=error_msg),
                    )
                    return

        except Exception as e:
            log.exception("Unexpected error reading Codex stream")
            await self._kill()
            yield StreamEvent(
                text_so_far=accumulated_text, done=True,
                response=ClaudeResponse(success=False, text=accumulated_text, error=str(e)),
            )

    async def _send_locked(self, prompt: str | list) -> AsyncIterator[StreamEvent]:
        """
        Core message-sending logic (must be called while holding self._lock).

        Handles the full lifecycle of a single Claude interaction:
        1. Ensure the subprocess is alive (start if needed)
        2. On the first message of a new session, prepend identity, memory,
           conversation history, and scheduling API context to the prompt
        3. When in a foreign workspace, prepend a per-message reminder to
           prevent Claude from acting on workspace context autonomously
        4. Write the JSON message to stdin and stream stdout line-by-line
        5. Parse stream-json events and yield StreamEvents to the caller

        Args:
            prompt: Either a text string or a list of content blocks (for
                multi-modal messages like images).

        Yields:
            StreamEvent objects with accumulated text. The final event has
            done=True and includes the complete ClaudeResponse.
        """
        # Route to Codex backend if configured
        if self.backend == "codex":
            async for event in self._send_codex_locked(prompt):
                yield event
            return

        try:
            await self._ensure_started()
        except FileNotFoundError:
            yield StreamEvent(
                text_so_far="",
                done=True,
                response=ClaudeResponse(success=False, text="", error="claude CLI not found"),
            )
            return

        # ── Fresh-session injection: full context on first message ──
        did_full_injection = False
        if self._fresh_session:
            self._fresh_session = False
            self._message_count = 0
            parts = self._build_context_injection()
            if parts:
                prefix = "\n\n".join(parts) + "\n\n"
                prompt = self._prepend_to_prompt(prompt, prefix)
                did_full_injection = True

        self._message_count += 1

        # ── B4: Proactive restart between messages to prevent compaction ──
        if self._needs_restart and not did_full_injection:
            log.info("Proactive restart: context window at %d tokens, restarting now", self._last_input_tokens)
            events.push("system", {"session_id": "", "restart": True, "reason": "proactive_context_cleanup"})
            await self._kill()
            self._needs_restart = False
            self._last_input_tokens = 0
            await self._ensure_started()
            self._fresh_session = False
            self._message_count = 1
            self._last_pushed_session_id = None
            parts = self._build_context_injection()
            if parts:
                prefix = "\n\n".join(parts) + "\n\n"
                prompt = self._prepend_to_prompt(prompt, prefix)
                did_full_injection = True

        # ── B2: Full re-injection if compaction was detected mid-stream ──
        if self._compacted_mid_stream and not did_full_injection:
            log.info("Re-injecting full context after mid-stream compaction")
            self._compacted_mid_stream = False
            parts = self._build_context_injection()
            if parts:
                parts.insert(0,
                    "[COMPACTION RECOVERY — your context was just compressed mid-response. "
                    "All core instructions and memory re-injected below.]"
                )
                prefix = "\n\n".join(parts) + "\n\n"
                prompt = self._prepend_to_prompt(prompt, prefix)
                did_full_injection = True

        # ── Per-message injection (survives mid-session compaction) ──
        # If RECOVERY.md exists, compaction happened — do a FULL re-injection
        # (same context as fresh session) so Claude has everything it needs.
        # On regular messages, inject only the TASKS focus block (~5-10 lines).
        recovery_path = self.home_workspace / ".memory" / "RECOVERY.md"
        if recovery_path.exists():
            try:
                recovery = recovery_path.read_text().strip()
                recovery_path.unlink(missing_ok=True)
                if recovery and not did_full_injection:
                    recovery_parts = self._build_context_injection()
                    recovery_parts.insert(0,
                        "[COMPACTION RECOVERY — your context was just compressed. "
                        "All core instructions and memory re-injected below. "
                        f"Pre-compact state:]\n{recovery}"
                    )
                    prefix = "\n\n".join(recovery_parts) + "\n\n"
                    prompt = self._prepend_to_prompt(prompt, prefix)
                elif recovery:
                    prompt = self._prepend_to_prompt(prompt,
                        f"[Recovery state from last compaction:]\n{recovery}\n\n"
                    )
            except OSError:
                pass
        else:
            tasks_path = self.home_workspace / ".memory" / "TASKS.md"
            # B3: Every REFRESH_INTERVAL messages, inject fuller context
            if (self._message_count % self.REFRESH_INTERVAL == 0) and not did_full_injection:
                refresh_parts = []
                if tasks_path.exists():
                    try:
                        refresh_parts.append(f"[Current tasks:]\n{tasks_path.read_text().strip()[:2000]}")
                    except OSError:
                        pass
                hacks_path = self.home_workspace / ".claude" / "HACKS.md"
                if hacks_path.exists():
                    try:
                        refresh_parts.append(f"[Workarounds:]\n{hacks_path.read_text().strip()[:1000]}")
                    except OSError:
                        pass
                from datetime import date
                log_path = self.home_workspace / ".memory" / "logs" / f"{date.today().isoformat()}.md"
                if log_path.exists():
                    try:
                        lines = log_path.read_text().strip().split("\n")
                        refresh_parts.append(f"[Recent log:]\n" + "\n".join(lines[-10:]))
                    except OSError:
                        pass
                if refresh_parts:
                    prefix = "[PERIODIC CONTEXT REFRESH — message #{0}:]\n".format(self._message_count)
                    prefix += "\n\n".join(refresh_parts) + "\n\n"
                    prompt = self._prepend_to_prompt(prompt, prefix)
                    log.info("Periodic context refresh at message %d", self._message_count)
            elif not did_full_injection:
                # Regular message — inject TASKS.md focus block for orientation
                if tasks_path.exists():
                    try:
                        focus = self._extract_tasks_focus(tasks_path.read_text())
                        if focus:
                            prompt = self._prepend_to_prompt(prompt,
                                f"[Current work state:]\n{focus}\n\n"
                            )
                    except OSError:
                        pass

        # When in a foreign workspace, remind on every message to only respond
        # to what the user asks — workspace context (CLAUDE.md, git branch,
        # auto-memory) can otherwise trigger autonomous action.
        if self.workspace != self.home_workspace:
            reminder = (
                "[IMPORTANT: This message is from a user via Telegram. "
                "Respond ONLY to what they wrote below. Do NOT continue, "
                "resume, or start any previous work, plans, or tasks.]"
            )
            if isinstance(prompt, str):
                prompt = reminder + "\n\n" + prompt
            elif isinstance(prompt, list):
                prompt = [{"type": "text", "text": reminder}] + prompt

        content = prompt if isinstance(prompt, list) else [{"type": "text", "text": prompt}]
        msg = (
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": content,
                    },
                }
            )
            + "\n"
        )

        # Log what we're sending to Claude (truncated for readability)
        prompt_preview = prompt[:200] if isinstance(prompt, str) else str(prompt)[:200]
        log.info("Sending prompt to Claude (len=%d): %s...", len(msg), prompt_preview)

        assert self._proc is not None
        assert self._proc.stdin is not None
        assert self._proc.stdout is not None
        try:
            self._proc.stdin.write(msg.encode())
            await self._proc.stdin.drain()
            log.info("Prompt written to Claude stdin, waiting for response stream...")
        except OSError as e:
            log.error("Failed to write to Claude process: %s", e)
            await self._kill()
            yield StreamEvent(
                text_so_far="",
                done=True,
                response=ClaudeResponse(
                    success=False, text="", error="Claude process died, restarting on next message"
                ),
            )
            return

        accumulated_text = ""
        try:
            while True:
                try:
                    # Opus doing complex tool chains (browser, subagents, research)
                    # can easily go 10-30+ minutes between stdout lines. The
                    # timeout here is a safety net for truly hung processes, not
                    # a limit on how long a task can take.
                    timeout = max(self.timeout_seconds * 5, 3600)
                    line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=timeout)
                except TimeoutError:
                    log.error(
                        "Claude silent for %ds — killing process (likely hung, not just slow)",
                        timeout,
                    )
                    await self._kill()
                    yield StreamEvent(
                        text_so_far=accumulated_text,
                        done=True,
                        response=ClaudeResponse(success=False, text=accumulated_text, error="Claude timed out"),
                    )
                    return
                except ValueError:
                    # asyncio.StreamReader.readline() raises ValueError when a
                    # single line exceeds the buffer limit. Skip the oversized
                    # line (likely a huge tool result) and keep reading.
                    log.warning("Skipping oversized stdout line (exceeded buffer limit)")
                    continue

                if not line:
                    # Process died unexpectedly
                    log.error("Claude process EOF")
                    await self._kill()
                    yield StreamEvent(
                        text_so_far=accumulated_text,
                        done=True,
                        response=ClaudeResponse(
                            success=bool(accumulated_text),
                            text=accumulated_text,
                            error=None if accumulated_text else "Claude process ended unexpectedly",
                        ),
                    )
                    return

                try:
                    event = json.loads(line.decode())
                except json.JSONDecodeError:
                    log.debug("Skipping non-JSON stdout line: %s", line.decode().strip()[:200])
                    continue

                etype = event.get("type")

                # Log stream events for debugging
                if etype == "system":
                    log.info("Claude stream: system (session=%s)", event.get("session_id", "?"))
                elif etype == "result":
                    log.info(
                        "Claude stream: result (cost=$%.4f, duration=%dms, error=%s)",
                        event.get("total_cost_usd", 0),
                        event.get("duration_ms", 0),
                        event.get("is_error", False),
                    )
                elif etype == "assistant":
                    msg_data = event.get("message", {})
                    if isinstance(msg_data, dict) and "content" in msg_data:
                        for block in msg_data.get("content", []):
                            btype = block.get("type")
                            if btype == "tool_use":
                                log.info(
                                    "Claude stream: tool_use [%s] (id=%s)",
                                    block.get("name", "?"),
                                    block.get("id", "?")[:12],
                                )
                            elif btype == "tool_result":
                                is_err = block.get("is_error", False)
                                log.info(
                                    "Claude stream: tool_result (id=%s, error=%s)",
                                    block.get("tool_use_id", "?")[:12],
                                    is_err,
                                )
                            elif btype == "text":
                                text_len = len(block.get("text", ""))
                                log.debug("Claude stream: text block (%d chars)", text_len)

                # Broadcast events to dashboard
                if etype == "assistant":
                    msg_data = event.get("message", {})
                    if isinstance(msg_data, dict) and "content" in msg_data:
                        for block in msg_data["content"]:
                            btype = block.get("type")
                            if btype == "text":
                                events.push("text", {"text": block.get("text", "")})
                            elif btype == "tool_use":
                                events.push("tool_use", {
                                    "tool": block.get("name", "unknown"),
                                    "id": block.get("id", ""),
                                    "input": block.get("input", {}),
                                })
                            elif btype == "tool_result":
                                events.push("tool_result", {
                                    "id": block.get("tool_use_id", ""),
                                    "output": str(block.get("content", ""))[:500],
                                    "is_error": block.get("is_error", False),
                                })
                            elif btype == "thinking":
                                events.push("thinking", {
                                    "thinking": block.get("thinking", block.get("text", "")),
                                })
                            else:
                                events.push(btype or "unknown", block)
                    elif isinstance(msg_data, str):
                        events.push("text", {"text": msg_data})
                    else:
                        events.push("raw", {"type": etype, "keys": list(event.keys()), "preview": str(event)[:500]})

                elif etype == "user":
                    # A2: Parse user events to extract tool_result content blocks
                    msg_data = event.get("message", {})
                    if isinstance(msg_data, dict):
                        content = msg_data.get("content", [])
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "tool_result":
                                    raw_content = block.get("content", "")
                                    if isinstance(raw_content, list):
                                        text_parts = [b.get("text", "") for b in raw_content if isinstance(b, dict)]
                                        output = "\n".join(text_parts)[:500]
                                    else:
                                        output = str(raw_content)[:500]
                                    events.push("tool_result", {
                                        "id": block.get("tool_use_id", ""),
                                        "output": output,
                                        "is_error": block.get("is_error", False),
                                    })

                elif etype == "result":
                    # Track token usage for proactive restart (B4)
                    usage = event.get("usage", {})
                    input_tokens = usage.get("input_tokens", 0)
                    if input_tokens > 0:
                        self._last_input_tokens = input_tokens
                        max_ctx = self._MAX_CONTEXT.get(self.model, 200_000)
                        if input_tokens > max_ctx * self.CONTEXT_RESTART_RATIO:
                            self._needs_restart = True
                            log.info(
                                "Context at %d/%d tokens (%.0f%%) — will restart between messages",
                                input_tokens, max_ctx, 100 * input_tokens / max_ctx,
                            )

                    events.push("result", {
                        "cost": event.get("total_cost_usd", 0),
                        "duration_ms": event.get("duration_ms", 0),
                        "num_turns": event.get("num_turns", 0),
                        "input_tokens": input_tokens,
                        "is_error": event.get("is_error", False),
                    })

                elif etype == "system":
                    sid = event.get("session_id", "")
                    # A3: Only push system event when session_id actually changes
                    if sid and sid != self._last_pushed_session_id:
                        # B2: Detect mid-stream compaction (session ID changes mid-response)
                        if self._last_pushed_session_id is not None:
                            self._compacted_mid_stream = True
                            events.push("compaction", {
                                "old_session": self._last_pushed_session_id[:8],
                                "new_session": sid[:8],
                                "message_count": self._message_count,
                            })
                            log.warning(
                                "Mid-stream compaction detected: session changed %s -> %s",
                                self._last_pushed_session_id[:8], sid[:8],
                            )
                        self._last_pushed_session_id = sid
                        events.push("system", {"session_id": sid})
                else:
                    events.push("raw", {"type": etype, "keys": list(event.keys()), "preview": str(event)[:500]})

                if etype == "system":
                    sid = event.get("session_id")
                    if sid:
                        self._session_id = sid

                elif etype == "result":
                    # Check for proactive restart after this response
                    if self._needs_restart:
                        log.info("Proactive restart flagged — will restart after this response completes")
                    # Prefer accumulated_text (which includes text before tool
                    # use) over the result event's text (which may only contain
                    # the final assistant message). Fall back to result_text
                    # when nothing was accumulated (e.g., system-only responses).
                    result_text = event.get("result", "")
                    text = accumulated_text if accumulated_text else result_text
                    response = ClaudeResponse(
                        success=not event.get("is_error", False),
                        text=text,
                        session_id=event.get("session_id", self._session_id),
                        cost_usd=event.get("total_cost_usd", 0.0),
                        duration_ms=event.get("duration_ms", 0),
                        error=event.get("result") if event.get("is_error") else None,
                    )
                    yield StreamEvent(text_so_far=response.text, done=True, response=response)
                    return

                elif etype == "assistant" and "message" in event:
                    msg_data = event["message"]
                    if isinstance(msg_data, dict) and "content" in msg_data:
                        for block in msg_data["content"]:
                            if block.get("type") == "text":
                                new_text = block.get("text", "")
                                if accumulated_text and new_text and not accumulated_text.endswith("\n"):
                                    accumulated_text += "\n\n"
                                accumulated_text += new_text
                                yield StreamEvent(text_so_far=accumulated_text)

                # Yield on every event so the caller can check its mid-stream
                # message queue.  Without this, long tool-use chains (Write,
                # Bash, Read …) that produce no assistant text block the
                # caller's async-for loop for minutes, starving the queue
                # drain in bot.py.  The yield is a no-op when accumulated_text
                # hasn't changed — the caller just gets a chance to run its
                # between-event housekeeping (mid-stream injection, /stop).
                if etype not in ("result",):  # result already yields + returns above
                    yield StreamEvent(text_so_far=accumulated_text)

        except Exception as e:
            log.exception("Unexpected error reading Claude stream")
            await self._kill()
            yield StreamEvent(
                text_so_far=accumulated_text,
                done=True,
                response=ClaudeResponse(success=False, text=accumulated_text, error=str(e)),
            )

    async def inject_message(self, text: str) -> bool:
        """
        Inject a user message into the Claude subprocess mid-stream.

        This writes a stream-json user message to stdin WITHOUT acquiring
        the send lock. It is only safe to call while _send_locked() already
        holds the lock and is reading from stdout — the message will be
        queued by Claude Code and processed after the current response.

        Returns True if the write succeeded, False if the process is dead.
        """
        if not self.is_alive or self._proc is None or self._proc.stdin is None:
            return False
        msg = (
            json.dumps({
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": text}],
                },
            })
            + "\n"
        )
        try:
            self._proc.stdin.write(msg.encode())
            await self._proc.stdin.drain()
            log.info("Injected mid-stream message (len=%d): %s...", len(text), text[:100])
            return True
        except OSError as e:
            log.error("Failed to inject mid-stream message: %s", e)
            return False

    def force_kill(self) -> None:
        """
        Kill the subprocess immediately. Safe to call without holding the lock.

        Called by /stop to abort an in-flight response. There is a race window
        between _ensure_started() and the stdin write in _send_locked(), but
        it is safe: killing the process causes EOF on stdout, which the
        streaming loop handles by yielding a done event and calling _kill()
        to clean up. No lock acquisition is needed here because _kill_proc()
        only sends a signal and is itself idempotent.
        """
        self._kill_proc(signal.SIGKILL)

    async def change_workspace(self, new_workspace: Path) -> None:
        """
        Switch the working directory for future Claude sessions.

        Kills the current process so the next send() call will restart
        Claude in the new directory. Called by /workspace command.

        Args:
            new_workspace: Path to the new working directory.
        """
        # No lock needed: _kill() terminates the process, and the next send()
        # call will start fresh in the new workspace via _ensure_started().
        # Any in-flight send() will see EOF on stdout and clean up.
        self.workspace = new_workspace
        await self._kill()

    async def restart(self) -> None:
        """
        Kill the current process so the next send() starts fresh.
        Called by /new command and model switches.
        """
        await self._kill()

    async def _kill(self) -> None:
        """
        Kill the subprocess and clean up resources.

        Sends SIGKILL, waits for the process to exit, clears the session ID,
        and cancels the stderr drain task. Idempotent - safe to call even if
        the process has already exited.
        """
        if self._proc:
            self._kill_proc(signal.SIGKILL)
            try:
                await self._proc.wait()
            except Exception:
                pass
            self._proc = None
            self._session_id = None
            self._last_pushed_session_id = None
        if self._stderr_task:
            self._stderr_task.cancel()
            self._stderr_task = None

    async def shutdown(self) -> None:
        """
        Gracefully shut down the Claude process.

        Sends SIGTERM first and waits up to 5 seconds for clean exit.
        Falls back to SIGKILL if the process doesn't terminate in time.
        Called during bot shutdown from main.py.
        """
        if self._proc and self._proc.returncode is None:
            self._kill_proc(signal.SIGTERM)
            try:
                # Note: when claude_user is set, self._proc is the sudo process.
                # SIGTERM is sent to the entire process group (sudo + claude), but
                # sudo may exit before claude finishes handling the signal. This
                # wait() returns when sudo exits, not necessarily when claude does.
                # In practice claude exits near-instantly after SIGTERM, but if
                # orphaned claude processes are ever observed after graceful
                # shutdown, this is the place to investigate.
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except TimeoutError:
                self._kill_proc(signal.SIGKILL)
                try:
                    # Timeout prevents blocking forever on a zombie process
                    await asyncio.wait_for(self._proc.wait(), timeout=5)
                except TimeoutError:
                    log.warning("Process did not exit after SIGKILL; abandoning")
        self._proc = None
        if self._stderr_task:
            self._stderr_task.cancel()
            self._stderr_task = None
