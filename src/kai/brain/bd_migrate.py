#!/usr/bin/env python3
"""
bd_migrate.py — Rank-4 behavioral-debt.yaml schema patch (text-based).

The existing behavioral-debt.yaml uses DSL-style strings like
  `count: "[OBSERVED].*auth attempt" >= 3`
that don't parse as pure YAML but are read as prose hints by Claude.
Round-tripping through PyYAML corrupts them. This migration does
TEXT-BASED surgical insertion instead: for each `- pattern_id:` block,
it inserts the new timestamp fields AFTER `recurrence_count:`.

Per the 2026-04-16 brain-memory consultation synthesis: both models
flagged the critical gap that `recurrence_count=7` could mean "fired 7
times this week" or "fired 7 times over 3 months" — the system cannot
distinguish healed patterns from fresh ones.

New fields added per pattern (ADDITIVE — keep `recurrence_count`):
    first_triggered: <ISO8601>
    last_triggered:  <ISO8601>
    trigger_history: [<ISO8601>, ...]  (capped at 20)
    halflife_days:   <float>           (derived from severity)

Back-fill policy (conservative — we can't recover real history):
    last_triggered  = now - 7 days
    first_triggered = last - (recurrence_count - 1) days
    trigger_history = evenly-spaced timestamps from first to last

Idempotent: if a pattern already has `last_triggered`, it's untouched.

Usage:
    python3 -m kai.brain.bd_migrate                # migrate in place
    python3 -m kai.brain.bd_migrate --dry-run      # show what would change
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BD_PATH = Path.home() / ".claude" / "behavioral-debt.yaml"

HALFLIFE_BY_SEVERITY = {1: 14, 2: 30, 3: 60, 4: 90, 5: 180}


def _iso(t: datetime) -> str:
    return t.isoformat(timespec="seconds")


def _now() -> datetime:
    return datetime.now(timezone.utc)


PATTERN_START_RE = re.compile(r"^\s*-\s+pattern_id:\s*(\S+)\s*$", re.MULTILINE)
RECURRENCE_RE = re.compile(r"^(\s*)recurrence_count:\s*(\d+)\s*$", re.MULTILINE)
SEVERITY_RE = re.compile(r"^(\s*)severity:\s*(\d+)\s*$", re.MULTILINE)


def migrate_text(raw: str, now: datetime | None = None) -> tuple[str, int]:
    """Return (new_text, patterns_migrated). Text-based surgical insertion."""
    now = now or _now()

    # Split into pattern blocks by finding each `- pattern_id:` line
    pattern_starts = [m.start() for m in PATTERN_START_RE.finditer(raw)]
    if not pattern_starts:
        return raw, 0

    # Section before the first pattern (comments + `patterns:` key)
    head = raw[:pattern_starts[0]]
    # Plus sentinel at end
    boundaries = pattern_starts + [len(raw)]

    blocks = []
    for i in range(len(pattern_starts)):
        blocks.append(raw[boundaries[i]:boundaries[i + 1]])

    migrated = 0
    new_blocks: list[str] = []
    for block in blocks:
        # Skip if already migrated
        if "last_triggered:" in block:
            new_blocks.append(block)
            continue
        sev_m = SEVERITY_RE.search(block)
        rec_m = RECURRENCE_RE.search(block)
        if not rec_m:
            # No recurrence_count — unusual; skip
            new_blocks.append(block)
            continue
        indent = rec_m.group(1)  # spaces before `recurrence_count:`
        recurrence = int(rec_m.group(2))
        severity = int(sev_m.group(2)) if sev_m else 3
        halflife = HALFLIFE_BY_SEVERITY.get(severity, 60)

        last = now - timedelta(days=7)
        first = last - timedelta(days=max(0, recurrence - 1))
        # Evenly spaced trigger_history, capped at 20
        if recurrence <= 1:
            history = [_iso(last)]
        else:
            span = (last - first).total_seconds()
            step = span / (recurrence - 1)
            history = [_iso(first + timedelta(seconds=step * i)) for i in range(recurrence)]
            history = history[-20:]

        # Build insertion text (YAML-compatible indentation matching recurrence_count level)
        insert = [
            f"{indent}first_triggered: \"{_iso(first)}\"",
            f"{indent}last_triggered:  \"{_iso(last)}\"",
            f"{indent}halflife_days:   {halflife}",
            f"{indent}trigger_history:",
        ] + [f"{indent}  - \"{ts}\"" for ts in history]
        insert_text = "\n" + "\n".join(insert)

        # Splice into block right after recurrence_count line
        insert_point = rec_m.end()
        # rec_m.end() is position WITHIN block (block was matched via re.search on block)
        new_block = block[:insert_point] + insert_text + block[insert_point:]
        new_blocks.append(new_block)
        migrated += 1

    # Update the Last-updated header comment
    head_lines = head.splitlines()
    new_head: list[str] = []
    for line in head_lines:
        if line.startswith("# Last updated:"):
            new_head.append(f"# Last updated: {now.date().isoformat()} (migrated: added timestamps + halflife per pattern)")
        else:
            new_head.append(line)
    head = "\n".join(new_head)
    if head and not head.endswith("\n"):
        head += "\n"

    new_text = head + "".join(new_blocks)
    return new_text, migrated


def migrate(dry_run: bool = False) -> int:
    if not BD_PATH.exists():
        print(f"[bd_migrate] {BD_PATH} not found", file=sys.stderr)
        return 1
    raw = BD_PATH.read_text(encoding="utf-8")
    new_text, migrated = migrate_text(raw)
    pattern_count = len(PATTERN_START_RE.findall(raw))
    print(f"[bd_migrate] patterns total: {pattern_count}", file=sys.stderr)
    print(f"[bd_migrate] patterns migrated: {migrated}", file=sys.stderr)
    print(f"[bd_migrate] bytes: {len(raw)} -> {len(new_text)}", file=sys.stderr)

    if dry_run:
        # Show diff on first migrated pattern
        if migrated == 0:
            print("[bd_migrate] DRY RUN — already migrated, no changes.", file=sys.stderr)
        else:
            import difflib
            diff = difflib.unified_diff(raw.splitlines(), new_text.splitlines(),
                                        fromfile="behavioral-debt.yaml",
                                        tofile="behavioral-debt.yaml (migrated)",
                                        n=2, lineterm="")
            for line in list(diff)[:50]:
                print(line)
        return 0

    BD_PATH.write_text(new_text, encoding="utf-8")
    print(f"[bd_migrate] wrote {BD_PATH}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return migrate(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
