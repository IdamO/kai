#!/usr/bin/env python3
"""
inject.py — Render top_of_mind.json into a compact injection block.

Consumed by claude.py `_build_context_injection()` as the FIRST item in the
injection stack, so the highest-salience atoms sit in the first-8K-token
attention window (per U-shaped attention literature; both models of the
2026-04-16 consultation cited this as the key constraint).

Output format: single markdown block, <= ~4 KB.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
TOP_OF_MIND = HOME / ".claude" / "shared" / "atoms" / "top_of_mind.json"

# Auto-refresh threshold: if top_of_mind.json older than this, regenerate
REFRESH_AFTER_SECONDS = 60 * 60  # 1 hour


def _maybe_refresh() -> bool:
    """Regenerate top_of_mind.json if stale. Return True if refresh succeeded or not needed."""
    if os.environ.get("KAI_BRAIN_NO_REFRESH"):
        return True
    needs = False
    if not TOP_OF_MIND.exists():
        needs = True
    else:
        age = time.time() - TOP_OF_MIND.stat().st_mtime
        if age > REFRESH_AFTER_SECONDS:
            needs = True
    if not needs:
        return True
    # Find kai source dir (this file is in src/kai/brain/inject.py)
    this = Path(__file__).resolve()
    kai_src = this.parent.parent.parent  # .../src
    env = {**os.environ, "PYTHONPATH": str(kai_src) + ":" + os.environ.get("PYTHONPATH", "")}
    try:
        subprocess.run(
            [sys.executable, "-m", "kai.brain.atomize", "--scope", "all"],
            env=env, check=True, capture_output=True, timeout=30,
        )
        subprocess.run(
            [sys.executable, "-m", "kai.brain.activate", "--budget", "80"],
            env=env, check=True, capture_output=True, timeout=30,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _age_label(ttl: str | None) -> str:
    if not ttl:
        return ""
    try:
        ttl_date = datetime.fromisoformat(ttl).date()
    except Exception:
        try:
            ttl_date = datetime.strptime(ttl, "%Y-%m-%d").date()
        except Exception:
            return ""
    today = datetime.now(timezone.utc).date()
    delta = (ttl_date - today).days
    if delta < 0:
        return f" EXPIRED {abs(delta)}d"
    if delta == 0:
        return " TODAY"
    if delta <= 3:
        return f" in {delta}d"
    if delta <= 14:
        return f" in {delta}d"
    return f" by {ttl}"


def _short_file(path: str) -> str:
    home = str(HOME)
    return path.replace(home, "~")


def _format_atom(e: dict) -> str:
    cls = e["volatility_class"]
    marker = {
        "identity":    "◆",
        "stable":      "●",
        "semi_stable": "◐",
        "operational": "○",
        "ephemeral":   "◦",
        "expired":     "✗",
    }.get(cls, "·")
    heading = (e.get("heading") or "").strip().replace("\n", " ")[:100]
    age = _age_label(e.get("ttl_hint"))
    source = _short_file(e.get("source_file", ""))
    line = e.get("source_line", "?")
    return f"{marker} [{cls:11s}] {heading}{age}\n    → {source}:{line}"


def build_injection_block(max_atoms: int = 40) -> str | None:
    """Return a short markdown block or None if top_of_mind.json missing."""
    _maybe_refresh()
    if not TOP_OF_MIND.exists():
        return None
    try:
        data = json.loads(TOP_OF_MIND.read_text())
    except Exception:
        return None

    atoms = data.get("top", [])[:max_atoms]
    if not atoms:
        return None

    meta = data.get("meta", {})
    generated = meta.get("generated_at", "")

    by_class: dict[str, list[dict]] = {}
    for a in atoms:
        by_class.setdefault(a["volatility_class"], []).append(a)

    lines: list[str] = []
    lines.append("[KAI BRAIN — Top of Mind (salience-ranked, decay-weighted)]")
    lines.append("")
    lines.append(f"Generated: {generated}  ·  "
                 f"Showing top {len(atoms)} of {meta.get('count', '?')} ranked atoms  ·  "
                 "Legend: ◆ identity · ● stable · ◐ semi-stable · ○ operational · ◦ ephemeral · ✗ expired")
    lines.append("Zombies + explicitly superseded atoms are filtered out (they live in ~/.claude/shared/atoms/superseded.jsonl).")
    lines.append("")

    # Put classes in priority order
    order = ["identity", "stable", "semi_stable", "operational", "ephemeral", "expired"]
    for cls in order:
        items = by_class.get(cls)
        if not items:
            continue
        lines.append(f"## {cls.upper()}")
        for a in items:
            lines.append(_format_atom(a))
        lines.append("")

    # Truth-layer pointers at the tail — these are the brain layer respecting the integrity layer
    truth_count = sum(1 for a in atoms if a.get("truth_links"))
    if truth_count:
        lines.append(f"[Note: {truth_count} atoms reference MODEL-/EXP-R-/DIAG- entities whose canonical "
                     f"values live in kyma-engine/manifests/*.yaml and docs/canonical/MANIFEST_CLAIMS.md. "
                     f"Never inline-cite those numbers from this summary — resolve via the manifest.]")
        lines.append("")

    lines.append("[END KAI BRAIN]")
    return "\n".join(lines)


if __name__ == "__main__":
    block = build_injection_block()
    if block:
        print(block)
    else:
        print("[no top_of_mind.json]")
