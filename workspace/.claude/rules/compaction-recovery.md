---
description: Post-compaction recovery protocol — re-read all core state files
globs: []
alwaysApply: true
---

# Compaction Recovery Rule

## Trigger
This rule activates after ANY context compaction or conversation continuation from a summary.

## Protocol (UNCONDITIONAL - never skip)
1. Read `.memory/RECOVERY.md` if it exists — it was written by the pre-compact hook with exact state at compaction time
2. Read `.memory/logs/{today}.md` — today's operational log with decisions, learnings, corrections, experiments. THIS IS YOUR PERSISTENT BRAIN. Trust it over the compaction summary.
3. Read `.memory/TASKS.md` — current work queue and focus
4. Read last 30 messages from `pending_messages` in `/Users/idamo/kai/kai.db`: `sqlite3 /Users/idamo/kai/kai.db "SELECT text, received_at FROM pending_messages WHERE processed = 0 ORDER BY received_at DESC LIMIT 30;"` — catches Telegram messages that arrived during or after compaction
5. Run `git status` — check for in-progress changes
6. Resume work from where it left off — do NOT ask the user to recap

## Daily Log = Your Persistent Brain (CRITICAL — added 2026-03-28)
The daily log is the ONLY operational state that survives compaction intact. Write to it BEFORE and AFTER every significant action:
- **BEFORE**: What you're about to do, why, expected duration, PIDs, file paths
- **AFTER**: Results, decisions made, what changed, next steps
This is how future-you recovers. TodoWrite is ephemeral. Conversation summaries are lossy. The daily log IS ground truth. If it's not in the log, it didn't happen.

## Why This Exists
Compaction summaries lose critical detail: exact file paths, error messages, partial progress, blocked tasks. The pre-compact hook captures disk state (git, files, processes) but NOT conversation context. Daily logs capture conversation context but only if entries were written during the session. Both together reconstruct full state.

## Mechanical Backup
claude.py performs full context re-injection (CLAUDE.md, MEMORY.md, TASKS.md, HACKS.md, today's log) when RECOVERY.md is detected. This rule is the behavioral layer on top of that mechanical safety net — read additional files the mechanical layer doesn't cover (rules/, specific project files being edited).

## Anti-Pattern
"The summary seems complete, I'll skip recovery steps" — this is ALWAYS wrong. The summary is lossy by definition. Read the source files.
