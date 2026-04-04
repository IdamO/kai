"""
Application entry point - initializes all subsystems and runs the Telegram bot.

Provides functionality to:
1. Configure logging with daily rotation and terminal output
2. Load configuration and validate environment
3. Initialize the database, Telegram bot, scheduled jobs, and webhook server
4. Restore workspace from previous session
5. Start the Telegram transport (webhook or polling, depending on config)
6. Notify the user if a previous response was interrupted by a crash
7. Run the event loop until shutdown (Ctrl+C or SIGTERM)
8. Clean up all resources in the correct order on exit

Telegram transport mode is determined by TELEGRAM_WEBHOOK_URL in .env:
    - Set: webhook mode (Telegram POSTs updates to Kai's HTTP server)
    - Unset: polling mode (Kai pulls updates from Telegram's servers)

The startup sequence is:
    1. Load config from .env
    2. Initialize SQLite database
    3. Create the Telegram bot application (with or without Updater)
    4. Restore previous workspace (if saved in settings table)
    5. Initialize the Telegram bot and register slash commands
    6. Load scheduled jobs from database into APScheduler
    7. Start the webhook HTTP server (always runs for scheduling API, GitHub webhooks, etc.)
    8. In webhook mode: register Telegram webhook with the API
       In polling mode: start the Updater's polling loop
    9. Check for interrupted-response flag file
    10. Block forever on asyncio.Event().wait()

The shutdown sequence (in the finally block) reverses this order:
    webhook server -> polling updater (if active) -> bot -> Claude process -> Telegram app -> database
"""

import asyncio
import fcntl
import logging
import os
import signal
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from telegram import BotCommand
from telegram.error import Conflict, NetworkError, TelegramError

from kai import cron, dashboard, services, sessions, webhook
from kai.bot import _is_workspace_allowed, create_bot
from kai.config import DATA_DIR, PROJECT_ROOT, _read_protected_file, load_config

# PID lock file — prevents two kai instances from running simultaneously.
# This is the structural fix for the Telegram Conflict error: even if launchd
# and the watchdog race, only one process can hold this lock.
_PID_LOCK_PATH = DATA_DIR / "kai.pid"
_pid_lock_file = None  # kept open for process lifetime


def setup_logging() -> None:
    """
    Configure root logger with file rotation and terminal output.

    Sets up two handlers on the root logger:
    - TimedRotatingFileHandler: writes to logs/kai.log, rotates at midnight,
      keeps 14 days of dated backups (kai.log.2026-02-12, etc.)
    - StreamHandler: writes to stderr for terminal visibility during `make run`
      (harmless under launchd since there's no terminal attached)

    Creates the logs/ directory if it doesn't already exist.
    """
    # Logs go under DATA_DIR so they're writable even when source is read-only
    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

    # Daily rotation at midnight, keep 2 weeks of history, use UTF-8 for
    # emoji and non-ASCII content in Claude responses
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "kai.log",
        when="midnight",
        backupCount=14,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Terminal output for interactive runs (make run, manual debugging)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    # Silence noisy per-request HTTP logs and APScheduler tick logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)


def _acquire_pid_lock() -> bool:
    """
    Acquire an exclusive PID lock to prevent duplicate instances.

    Uses fcntl.flock (not a PID file check) so the lock is automatically
    released if the process crashes, is killed, or exits — no stale lock
    files to clean up. Returns True if lock acquired, False if another
    instance holds it.
    """
    global _pid_lock_file
    _PID_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    _pid_lock_file = open(_PID_LOCK_PATH, "w")
    try:
        fcntl.flock(_pid_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _pid_lock_file.write(str(os.getpid()))
        _pid_lock_file.flush()
        return True
    except OSError:
        _pid_lock_file.close()
        _pid_lock_file = None
        return False


def main() -> None:
    """
    Top-level entry point for the Kai bot.

    Sets up logging, loads configuration, and delegates to an async
    initialization function that manages the full application lifecycle.
    Catches KeyboardInterrupt for clean Ctrl+C shutdown and logs any
    unexpected crashes.
    """
    setup_logging()

    # Log signal-based kills so we know WHY kai died (watchdog kickstart -k
    # sends SIGTERM, then SIGKILL after grace period)
    def _signal_handler(signum: int, _frame: object) -> None:
        sig_name = signal.Signals(signum).name
        logging.info("Kai received %s (signal %d) — shutting down", sig_name, signum)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGHUP, _signal_handler)

    # Acquire PID lock BEFORE doing anything else. If another instance
    # is running, exit immediately — launchd will retry later.
    if not _acquire_pid_lock():
        logging.error("Another Kai instance is already running (lock held on %s). Exiting.", _PID_LOCK_PATH)
        sys.exit(1)

    config = load_config()
    logging.info("Kai starting (model=%s, users=%s, pid=%d)", config.claude_model, config.allowed_user_ids, os.getpid())

    # Load external service definitions. In a protected installation, services.yaml
    # lives in /etc/kai/ (root-owned). Falls back to PROJECT_ROOT for development.
    protected_yaml = _read_protected_file("/etc/kai/services.yaml")
    if protected_yaml:
        loaded = services.load_services_from_string(protected_yaml)
    else:
        loaded = services.load_services(PROJECT_ROOT / "services.yaml")
    if loaded:
        names = ", ".join(loaded.keys())
        logging.info("Loaded %d service(s): %s", len(loaded), names)

    async def _init_and_run() -> None:
        """
        Async initialization and main event loop.

        Initializes all subsystems (database, bot, scheduler, webhooks),
        restores previous state, and blocks until shutdown. The finally
        block ensures all resources are cleaned up in reverse order.
        """
        # Derive transport mode from config: webhook if URL is set, polling otherwise
        use_webhook = config.telegram_webhook_url is not None

        await sessions.init_db(config.session_db_path)
        app = create_bot(config, use_webhook=use_webhook)

        # Restore workspace from previous session (persisted in settings table)
        saved_workspace = await sessions.get_setting("workspace")
        if saved_workspace:
            ws_path = Path(saved_workspace)
            if not _is_workspace_allowed(ws_path, config):
                logging.warning(
                    "Saved workspace %s is not under WORKSPACE_BASE or ALLOWED_WORKSPACES, ignoring",
                    saved_workspace,
                )
                await sessions.delete_setting("workspace")
            elif ws_path.is_dir():
                await app.bot_data["claude"].change_workspace(ws_path)
                logging.info("Restored workspace: %s", ws_path)
            else:
                logging.warning("Saved workspace no longer exists: %s", saved_workspace)
                await sessions.delete_setting("workspace")

        try:
            # Retry initialization if the network isn't ready yet (e.g. after a
            # power outage where DNS may take a while to come back).
            for attempt in range(1, 13):
                try:
                    await app.initialize()
                    break
                except NetworkError:
                    if attempt == 12:
                        raise
                    wait = min(30, 2**attempt)
                    logging.warning(
                        "Network not ready (attempt %d/12), retrying in %ds…",
                        attempt,
                        wait,
                    )
                    await asyncio.sleep(wait)

            await app.start()

            # Register slash command menu in Telegram's bot command list
            await app.bot.set_my_commands(
                [
                    BotCommand("models", "Choose a model"),
                    BotCommand("model", "Switch model (opus, sonnet, haiku)"),
                    BotCommand("new", "Start a fresh session"),
                    BotCommand("workspace", "Switch working directory"),
                    BotCommand("workspaces", "List recent workspaces"),
                    BotCommand("stop", "Interrupt current response"),
                    BotCommand("stats", "Show session info and cost"),
                    BotCommand("jobs", "List scheduled jobs"),
                    BotCommand("canceljob", "Cancel a scheduled job"),
                    BotCommand("voice", "Toggle voice responses / set voice"),
                    BotCommand("voices", "Choose a voice (inline buttons)"),
                    BotCommand("webhooks", "Show webhook server status"),
                    BotCommand("help", "Show available commands"),
                ]
            )

            # Reload scheduled jobs from the database into APScheduler
            await cron.init_jobs(app)
            await cron.start_task_drain(app)

            # Start the HTTP server (always runs - serves scheduling API, GitHub
            # webhooks, file exchange, and health check regardless of transport mode).
            # In webhook mode, this also registers the Telegram webhook with the API.
            await webhook.start(app, config)
            await dashboard.start(port=3456)
            # webhook.start() initializes the confinement path from config (home workspace).
            # If a non-default workspace was restored above, sync it now so send-file
            # accepts files from the restored workspace. Must come after start() because
            # start() would overwrite any earlier update_workspace() call.
            if app.bot_data["claude"].workspace != config.claude_workspace:
                webhook.update_workspace(str(app.bot_data["claude"].workspace))

            # In polling mode, start the Updater's long-polling loop. PTB's
            # start_polling() automatically calls delete_webhook() first, which
            # cleans up any stale webhook from a previous webhook-mode run.
            #
            # Retry with backoff to survive the Telegram Conflict window: after
            # a kill, the old polling session stays valid server-side for up to
            # ~30s. Rather than crashing, we wait it out.
            if not use_webhook:
                assert app.updater is not None

                # Nuclear session cleanup before polling:
                # 1. deleteWebhook(drop_pending_updates=True) tells Telegram to
                #    discard any in-flight getUpdates and release the session.
                # 2. bot.close() closes the local HTTP connection pool.
                # 3. Short sleep lets Telegram's servers fully release.
                # This replaces the old bot.close() + 12s sleep which was insufficient.
                try:
                    await app.bot.delete_webhook(drop_pending_updates=True)
                    logging.info("Deleted webhook + dropped pending updates")
                except Exception as e:
                    logging.warning("delete_webhook failed: %s", e)
                try:
                    await app.bot.close()
                    logging.info("Closed previous bot session")
                except Exception as e:
                    logging.warning("bot.close() failed (probably no prior session): %s", e)

                # Short sleep after nuclear cleanup (3s is enough now that we've
                # told Telegram to drop the session, vs 12s when we only closed locally)
                await asyncio.sleep(3)

                _conflict_count = 0

                def _polling_error_callback(error: TelegramError) -> None:
                    """Suppress Conflict errors during polling (self-healing noise).

                    After rapid kill/restart cycles, Telegram's server-side connection
                    takes up to ~30s to expire. PTB retries internally and recovers,
                    but dumps full tracebacks to stderr on every retry. This callback
                    intercepts those and logs at WARNING (first 3) then DEBUG to keep
                    logs readable. Non-Conflict errors still get full ERROR logging.
                    """
                    nonlocal _conflict_count
                    if isinstance(error, Conflict):
                        _conflict_count += 1
                        if _conflict_count <= 3:
                            logging.warning(
                                "Polling Conflict #%d (self-healing, PTB retries internally): %s",
                                _conflict_count,
                                error,
                            )
                        else:
                            logging.debug("Polling Conflict #%d (suppressed): %s", _conflict_count, error)
                    else:
                        logging.error("Polling error: %s", error, exc_info=error)

                for poll_attempt in range(1, 7):
                    try:
                        await app.updater.start_polling(
                            allowed_updates=["message", "callback_query"],
                            error_callback=_polling_error_callback,
                        )
                        logging.info("Polling started")
                        break
                    except Conflict:
                        if poll_attempt == 6:
                            raise
                        wait = poll_attempt * 5
                        logging.warning(
                            "Telegram Conflict (previous session still active), "
                            "retrying in %ds (attempt %d/6)",
                            wait,
                            poll_attempt,
                        )
                        await asyncio.sleep(wait)

            # Check if a previous response was interrupted by a crash/restart.
            # bot.py writes this flag file when it starts processing a message
            # and deletes it when done. If it exists at startup, the process
            # crashed mid-response and the user should be notified.
            # Flag file is under DATA_DIR (writable) not PROJECT_ROOT (may be read-only)
            flag = DATA_DIR / ".responding_to"
            try:
                chat_id = int(flag.read_text().strip())
                await app.bot.send_message(
                    chat_id, "Sorry, my previous response was interrupted. Please resend your last message."
                )
                logging.info("Notified chat %d of interrupted response", chat_id)
                flag.unlink(missing_ok=True)
            except FileNotFoundError:
                pass
            except Exception:
                # Full traceback helps diagnose issues like corrupt flag file content
                logging.exception("Failed to send interrupted-response notice")
                flag.unlink(missing_ok=True)

            # Notify user about unprocessed messages but leave them in DB
            # with processed=0.  The _handle_message lock-acquisition drain
            # and the pre-send drain in _handle_response will prepend them
            # to the next prompt so Claude actually sees them.
            try:
                async with sessions._get_db().execute(
                    "SELECT DISTINCT chat_id FROM pending_messages WHERE processed = 0"
                ) as cursor:
                    chats_with_pending = [row[0] for row in await cursor.fetchall()]
                for pending_chat_id in chats_with_pending:
                    pending = await sessions.get_pending_messages(pending_chat_id)
                    if pending:
                        texts = [m["text"] for m in pending]
                        lines = "\n".join(f"  {i+1}. {t[:120]}" for i, t in enumerate(texts))
                        await app.bot.send_message(
                            pending_chat_id,
                            f"I restarted. {len(texts)} undelivered message(s) will be included in my next response:\n{lines}",
                        )
                        # Do NOT mark processed here - let the handler drains do it
                        logging.info("Found %d pending messages for chat %d (will drain on next send)", len(texts), pending_chat_id)
            except Exception:
                logging.exception("Failed to drain pending messages")

            # Clean up old processed messages
            try:
                await sessions.cleanup_old_messages(days=7)
            except Exception:
                pass

            logging.info("Kai is running. Press Ctrl+C to stop.")

            # Polling health monitor: PTB's polling loop silently dies on DNS
            # errors and never recovers (despite claiming max_retries=-1).
            # The process stays alive with health 200 but can't receive messages.
            # This monitor detects the dead polling task and force-exits so
            # launchd KeepAlive restarts the process immediately.
            if not use_webhook and app.updater is not None:
                async def _polling_health_monitor() -> None:
                    await asyncio.sleep(60)  # grace period after startup
                    while True:
                        await asyncio.sleep(60)  # check every 60 seconds
                        try:
                            # Access the internal polling task
                            task = app.updater._Updater__polling_task  # type: ignore[attr-defined]
                            if task is not None and task.done():
                                exc = task.exception() if not task.cancelled() else None
                                # Conflict errors are self-healing. PTB retries
                                # internally. Do NOT force-exit on Conflict.
                                if exc and "Conflict" in str(exc):
                                    logging.warning(
                                        "Polling task has Conflict error (self-healing, not force-exiting): %s",
                                        exc,
                                    )
                                    continue
                                logging.error(
                                    "Polling task died (exception=%s). Force-exiting for launchd restart.",
                                    exc,
                                )
                                import os
                                os._exit(1)
                        except Exception:
                            logging.exception("Polling health monitor error")

                asyncio.create_task(
                    _polling_health_monitor(),
                    name="polling_health_monitor",
                )

            await asyncio.Event().wait()  # Block forever until shutdown signal
        finally:
            # Clean the interrupted-response flag on graceful shutdown.
            # This flag should only persist across CRASHES, not clean restarts
            # from watchdog/launchd/SIGTERM. If we reach this finally block,
            # the shutdown is orderly — no need to spam "response was interrupted".
            flag = DATA_DIR / ".responding_to"
            flag.unlink(missing_ok=True)

            # Shutdown in reverse order of startup
            await dashboard.stop()
            await webhook.stop()
            # Stop the polling Updater if it was running (no-op in webhook mode
            # since the Updater was suppressed at build time)
            if not use_webhook and app.updater:
                await app.updater.stop()
            await app.stop()
            await app.bot_data["claude"].shutdown()
            await app.shutdown()
            await sessions.close_db()

    try:
        asyncio.run(_init_and_run())
    except KeyboardInterrupt:
        logging.info("Kai stopped.")
    except Exception:
        logging.exception("Kai crashed")


if __name__ == "__main__":
    main()
