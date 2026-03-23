#!/bin/bash
# Kai Watchdog — checks if Kai is healthy, force-restarts if stuck
# Runs every 2 minutes via LaunchAgent
#
# Known failure modes:
# - DNS dies (road trip WiFi), polling loop crashes, never recovers even after DNS returns
# - Health endpoint stays 200 (local), cron jobs fire (independent), but no messages get through
# - Playwright Chrome processes accumulate and eat CPU

LOG="/Users/idamo/kai/logs/kai.log"
HEALTH="http://localhost:8080/health"
FAIL_FILE="/tmp/kai-watchdog-failures"
MAX_FAILURES=3

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
        logger -t kai-watchdog "DNS broken for $FAILS checks, flushing DNS and restarting Kai"
        dscacheutil -flushcache 2>/dev/null
        killall -HUP mDNSResponder 2>/dev/null
        sleep 2
        launchctl kickstart -k gui/$(id -u)/com.kai.telegram
        reset_failures
    fi
    exit 0
fi

# 4. Check if webhook server responds
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$HEALTH" 2>/dev/null)
if [ "$HTTP_CODE" = "000" ]; then
    FAILS=$(increment_failures)
    logger -t kai-watchdog "Webhook unresponsive (attempt $FAILS/$MAX_FAILURES)"
    if [ "$FAILS" -ge "$MAX_FAILURES" ]; then
        logger -t kai-watchdog "Webhook dead for $FAILS checks, restarting Kai"
        launchctl kickstart -k gui/$(id -u)/com.kai.telegram
        reset_failures
    fi
    exit 0
fi

# 5. CRITICAL: Detect dead polling loop
#    Polling dies from DNS/network errors but process stays alive.
#    Detection: polling errors exist AFTER the last "Polling started" timestamp.
if [ -f "$LOG" ]; then
    LAST_POLL_START=$(grep "Polling started" "$LOG" | tail -1 | cut -d' ' -f1,2 | cut -d',' -f1)
    LAST_POLL_ERROR=$(grep "Exception happened while polling" "$LOG" | tail -1 | cut -d' ' -f1,2 | cut -d',' -f1)

    if [ -n "$LAST_POLL_START" ] && [ -n "$LAST_POLL_ERROR" ]; then
        START_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_POLL_START" +%s 2>/dev/null)
        ERROR_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_POLL_ERROR" +%s 2>/dev/null)
        NOW=$(date +%s)

        if [ -n "$START_EPOCH" ] && [ -n "$ERROR_EPOCH" ]; then
            START_AGE=$((NOW - START_EPOCH))
            if [ "$ERROR_EPOCH" -gt "$START_EPOCH" ] && [ "$START_AGE" -gt 180 ]; then
                logger -t kai-watchdog "DEAD POLLING LOOP: last start ${START_AGE}s ago, errors after start. Restarting."
                launchctl kickstart -k gui/$(id -u)/com.kai.telegram
                reset_failures
                exit 0
            fi
        fi
    fi
fi

# 6. Check for active polling error spam
if [ -f "$LOG" ]; then
    RECENT_ERRORS=$(tail -200 "$LOG" 2>/dev/null | grep -c "Exception happened while polling")
    RECENT_ERRORS=${RECENT_ERRORS:-0}
    if [ "$RECENT_ERRORS" -gt 5 ] 2>/dev/null; then
        FAILS=$(increment_failures)
        logger -t kai-watchdog "Kai has $RECENT_ERRORS polling errors (attempt $FAILS/$MAX_FAILURES)"
        if [ "$FAILS" -ge "$MAX_FAILURES" ]; then
            logger -t kai-watchdog "Persistent polling errors, restarting Kai"
            launchctl kickstart -k gui/$(id -u)/com.kai.telegram
            reset_failures
        fi
        exit 0
    fi
fi

# 7. Clean up idle Playwright Chrome (>15 min old)
for PID in $(ps axo pid,args | grep "mcp-chrome" | grep -v grep | awk '{print $1}'); do
    ETIME=$(ps -o etime= -p "$PID" 2>/dev/null | xargs)
    [ -z "$ETIME" ] && continue

    # Parse etime to seconds: [[dd-]hh:]mm:ss
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
reset_failures
exit 0
