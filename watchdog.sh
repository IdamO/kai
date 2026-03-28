#!/bin/bash
# Kai Watchdog — checks if Kai is healthy, force-restarts if stuck
# Runs every 2 minutes via LaunchAgent
#
# Known failure modes:
# - DNS dies (road trip WiFi), polling loop crashes, never recovers even after DNS returns
# - Health endpoint stays 200 (local), cron jobs fire (independent), but no messages get through
# - Playwright Chrome processes accumulate and eat CPU
#
# CRITICAL: launchd KeepAlive=true already handles process crashes.
# The watchdog only handles the SUBTLE case where the process is alive but broken
# (dead polling loop, unresponsive webhook). It must NEVER race with launchd.
# All restarts use a cooldown lock to prevent double-start conflicts.

LOG="/Users/idamo/kai/logs/kai.log"
WDLOG="/Users/idamo/kai/logs/watchdog-debug.log"
HEALTH="http://localhost:8080/health"
FAIL_FILE="/tmp/kai-watchdog-failures"
RESTART_LOCK="/tmp/kai-restart-lock"
MAX_FAILURES=3
# Cooldown: don't restart if we restarted within the last 60 seconds
RESTART_COOLDOWN=60

get_failures() {
    cat "$FAIL_FILE" 2>/dev/null || echo 0
}

increment_failures() {
    local COUNT
    COUNT=$(get_failures)
    COUNT=$((COUNT + 1))
    echo "$COUNT" > "$FAIL_FILE"
    echo "$COUNT"
}

reset_failures() {
    echo 0 > "$FAIL_FILE"
}

safe_restart() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') safe_restart called: $1" >> "$WDLOG"
    # Prevent racing with launchd KeepAlive by using a cooldown lock.
    if [ -f "$RESTART_LOCK" ]; then
        LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$RESTART_LOCK" 2>/dev/null || echo 0) ))
        if [ "$LOCK_AGE" -lt "$RESTART_COOLDOWN" ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') safe_restart: SKIPPED (cooldown ${LOCK_AGE}s < ${RESTART_COOLDOWN}s)" >> "$WDLOG"
            logger -t kai-watchdog "Skipping restart — cooldown active (${LOCK_AGE}s < ${RESTART_COOLDOWN}s)"
            return 1
        fi
    fi

    # Check how many Kai instances are running BEFORE restarting
    KAI_COUNT=$(pgrep -f "python.*-m kai" | wc -l | tr -d ' ')
    echo "$(date '+%Y-%m-%d %H:%M:%S') safe_restart: kai_count=$KAI_COUNT" >> "$WDLOG"
    if [ "$KAI_COUNT" -gt 1 ]; then
        logger -t kai-watchdog "CONFLICT: $KAI_COUNT Kai instances running. Killing all, launchd will restart."
        echo "$(date '+%Y-%m-%d %H:%M:%S') safe_restart: KILLING ALL ($KAI_COUNT instances)" >> "$WDLOG"
        pkill -9 -f "python.*-m kai"
        touch "$RESTART_LOCK"
        reset_failures
        return 0
    fi

    # Single instance but broken — use kickstart -k (kills + restarts atomically)
    logger -t kai-watchdog "$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') safe_restart: KICKSTARTING (single instance)" >> "$WDLOG"
    rm -f /Users/idamo/kai/.responding_to 2>/dev/null
    touch "$RESTART_LOCK"
    launchctl kickstart -k gui/$(id -u)/com.kai.telegram
    reset_failures
}

echo "$(date '+%Y-%m-%d %H:%M:%S') === WATCHDOG RUN ===" >> "$WDLOG"

# 0. PRE-CHECK: Detect and fix multiple instances (the Conflict bug)
# Kai now holds an fcntl lock on kai.pid — duplicates exit immediately.
# pgrep can catch a duplicate during its brief startup (before lock rejection),
# so we require BOTH processes to be older than 10s before considering it a real
# conflict. Brief duplicates (launchd double-start, slow PID lock) are harmless.
KAI_PIDS=$(pgrep -f "python.*-m kai")
KAI_COUNT=$(echo "$KAI_PIDS" | grep -c .)
if [ "$KAI_COUNT" -gt 1 ]; then
    # Check if all processes are established (>10s old), not just spawning
    OLD_COUNT=0
    for PID in $KAI_PIDS; do
        ETIME=$(ps -o etime= -p "$PID" 2>/dev/null | xargs)
        [ -z "$ETIME" ] && continue
        # Parse elapsed time to seconds
        SECS=0
        if echo "$ETIME" | grep -q '-'; then
            DAYS=$(echo "$ETIME" | cut -d'-' -f1)
            ETIME=$(echo "$ETIME" | cut -d'-' -f2)
            SECS=$((DAYS * 86400))
        fi
        IFS=':' read -ra P <<< "$ETIME"
        case ${#P[@]} in
            3) SECS=$((SECS + 10#${P[0]} * 3600 + 10#${P[1]} * 60 + 10#${P[2]})) ;;
            2) SECS=$((SECS + 10#${P[0]} * 60 + 10#${P[1]})) ;;
            1) SECS=$((SECS + 10#${P[0]})) ;;
        esac
        if [ "$SECS" -gt 10 ] 2>/dev/null; then
            OLD_COUNT=$((OLD_COUNT + 1))
        fi
    done
    if [ "$OLD_COUNT" -gt 1 ]; then
        logger -t kai-watchdog "CONFLICT DETECTED: $OLD_COUNT established instances (>10s). Killing all."
        pkill -9 -f "python.*-m kai"
        rm -f /Users/idamo/kai/.responding_to 2>/dev/null
        touch "$RESTART_LOCK"
        sleep 5
        exit 0
    elif [ "$OLD_COUNT" -le 1 ] && [ "$KAI_COUNT" -gt 1 ]; then
        logger -t kai-watchdog "Brief duplicate detected ($KAI_COUNT pids, $OLD_COUNT established). PID lock will handle it."
    fi
fi

# 1. Check if Kai process exists at all
if ! launchctl list | grep -q "com.kai.telegram"; then
    logger -t kai-watchdog "Kai not in launchctl, bootstrapping"
    launchctl bootstrap gui/$(id -u) /Users/idamo/Library/LaunchAgents/com.kai.telegram.plist 2>/dev/null
    exit 0
fi

# 2. Check basic internet
if ! ping -c 1 -t 3 8.8.8.8 >/dev/null 2>&1; then
    logger -t kai-watchdog "No internet connectivity, skipping checks"
    exit 0
fi

# 3. Check DNS resolution
if ! host -W 3 api.telegram.org >/dev/null 2>&1; then
    FAILS=$(increment_failures)
    logger -t kai-watchdog "DNS failing (attempt $FAILS/$MAX_FAILURES)"
    if [ "$FAILS" -ge "$MAX_FAILURES" ]; then
        dscacheutil -flushcache 2>/dev/null
        killall -HUP mDNSResponder 2>/dev/null
        sleep 2
        safe_restart "DNS broken for $FAILS checks, restarting Kai"
    fi
    exit 0
fi

# 4. Check if webhook server responds
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$HEALTH" 2>/dev/null)
if [ "$HTTP_CODE" = "000" ]; then
    FAILS=$(increment_failures)
    logger -t kai-watchdog "Webhook unresponsive (attempt $FAILS/$MAX_FAILURES)"
    if [ "$FAILS" -ge "$MAX_FAILURES" ]; then
        safe_restart "Webhook dead for $FAILS checks, restarting Kai"
    fi
    exit 0
fi

# 5. CRITICAL: Detect dead polling loop
#    Polling dies from DNS/network errors but process stays alive.
#    Detection: non-Conflict "Exception happened while polling" in RECENT log lines
#    (last 200) AFTER the last "Polling started".
#    BUG FIX 2026-03-26: was searching entire log file, so one historical non-Conflict
#    error would permanently trigger restarts. Now uses tail -200 like step 6.
if [ -f "$LOG" ]; then
    LAST_POLL_START=$(tail -200 "$LOG" | grep "Polling started" | tail -1 | cut -d' ' -f1,2 | cut -d',' -f1)
    RECENT_POLL_ERRORS=$(tail -200 "$LOG" 2>/dev/null | grep -c "Exception happened while polling")
    RECENT_CONFLICT_LINES=$(tail -200 "$LOG" 2>/dev/null | grep -c "telegram.error.Conflict")
    echo "$(date '+%Y-%m-%d %H:%M:%S') step5: poll_start=$LAST_POLL_START poll_errs=$RECENT_POLL_ERRORS conflicts=$RECENT_CONFLICT_LINES" >> "$WDLOG"
    if [ "$RECENT_CONFLICT_LINES" -ge "$RECENT_POLL_ERRORS" ] 2>/dev/null; then
        LAST_POLL_ERROR=""
    else
        LAST_POLL_ERROR=$(tail -200 "$LOG" | grep "Exception happened while polling" | tail -1 | cut -d' ' -f1,2 | cut -d',' -f1)
    fi

    if [ -n "$LAST_POLL_START" ] && [ -n "$LAST_POLL_ERROR" ]; then
        START_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_POLL_START" +%s 2>/dev/null || echo "")
        ERROR_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_POLL_ERROR" +%s 2>/dev/null || echo "")
        NOW=$(date +%s)

        if [ -n "$START_EPOCH" ] && [ -n "$ERROR_EPOCH" ]; then
            START_AGE=$((NOW - START_EPOCH))
            echo "$(date '+%Y-%m-%d %H:%M:%S') step5: start_age=${START_AGE}s error_after_start=$( [ "$ERROR_EPOCH" -gt "$START_EPOCH" ] && echo yes || echo no )" >> "$WDLOG"
            if [ "$ERROR_EPOCH" -gt "$START_EPOCH" ] && [ "$START_AGE" -gt 300 ]; then
                echo "$(date '+%Y-%m-%d %H:%M:%S') step5: TRIGGERING RESTART" >> "$WDLOG"
                safe_restart "DEAD POLLING LOOP: last start ${START_AGE}s ago, errors after start"
                exit 0
            fi
        fi
    fi
fi

# 6. Check for active polling error spam — EXCLUDE Conflict errors.
# Conflict errors are self-healing (PTB retries with backoff) and the watchdog
# restarting on Conflict CAUSES the next Conflict (restart loop). Only act on
# non-Conflict polling exceptions (DNS, network, timeout).
if [ -f "$LOG" ]; then
    # Count non-Conflict polling errors. "Conflict" appears ~20 lines AFTER
    # "Exception happened while polling" in the traceback. Simple approach:
    # count total polling errors AND total Conflict lines. If they match,
    # ALL errors are Conflict (harmless, self-healing). Only act if there
    # are polling errors that AREN'T Conflict.
    TOTAL_POLL_ERRORS=$(tail -200 "$LOG" 2>/dev/null | grep -c "Exception happened while polling")
    TOTAL_CONFLICTS=$(tail -200 "$LOG" 2>/dev/null | grep -c "telegram.error.Conflict")
    # If every polling error has a corresponding Conflict line, they're all Conflict
    if [ "$TOTAL_CONFLICTS" -ge "$TOTAL_POLL_ERRORS" ] 2>/dev/null; then
        RECENT_ERRORS=0
    else
        RECENT_ERRORS=$((TOTAL_POLL_ERRORS - TOTAL_CONFLICTS))
    fi
    RECENT_ERRORS=${RECENT_ERRORS:-0}
    RECENT_ERRORS=${RECENT_ERRORS:-0}
    if [ "$RECENT_ERRORS" -gt 5 ] 2>/dev/null; then
        FAILS=$(increment_failures)
        logger -t kai-watchdog "Kai has $RECENT_ERRORS polling errors (attempt $FAILS/$MAX_FAILURES)"
        if [ "$FAILS" -ge "$MAX_FAILURES" ]; then
            safe_restart "Persistent polling errors ($RECENT_ERRORS in last 200 lines)"
        fi
        exit 0
    fi
fi

# 7. Clean up idle Playwright Chrome (>15 min old)
for PID in $(ps axo pid,args | grep "mcp-chrome" | grep -v grep | awk '{print $1}'); do
    ETIME=$(ps -o etime= -p "$PID" 2>/dev/null | xargs)
    [ -z "$ETIME" ] && continue

    SECS=0
    if echo "$ETIME" | grep -q '-'; then
        DAYS=$(echo "$ETIME" | cut -d'-' -f1)
        ETIME=$(echo "$ETIME" | cut -d'-' -f2)
        SECS=$((DAYS * 86400))
    fi
    IFS=':' read -ra P <<< "$ETIME"
    case ${#P[@]} in
        3) SECS=$((SECS + 10#${P[0]} * 3600 + 10#${P[1]} * 60 + 10#${P[2]})) ;;
        2) SECS=$((SECS + 10#${P[0]} * 60 + 10#${P[1]})) ;;
        1) SECS=$((SECS + 10#${P[0]})) ;;
    esac

    if [ "$SECS" -gt 900 ] 2>/dev/null; then
        logger -t kai-watchdog "Killing idle Playwright Chrome (PID $PID, ${SECS}s)"
        kill "$PID" 2>/dev/null
    fi
done

# All checks passed
echo "$(date '+%Y-%m-%d %H:%M:%S') ALL CHECKS PASSED — no restart" >> "$WDLOG"
reset_failures
exit 0
