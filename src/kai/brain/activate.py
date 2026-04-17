#!/usr/bin/env python3
"""
activate.py — Rank 2 (temporal validity + TTL auto-expire) +
              Rank 3 (ACT-R activation + top_of_mind.json ranked view)
combined, because they share the same input (atom index) and same output
channel (injected context).

Per the 2026-04-16 brain-memory consultation synthesis:

Rank 2 — temporal validity classifier + TTL auto-expire (~3 hrs)
    - 5-class taxonomy {identity, stable, semi_stable, operational, ephemeral}
    - Decay rates d ∈ {0.05, 0.15, 0.35, 0.50, 0.80}
    - Deadline regex → ttl_hint → reclassify to ephemeral when past
    - Strong-topic promotion: atoms with MODEL-\\d{3} / EXP-R\\d+ get
      more stable class so canonical facts don't age out

Rank 3 — activation compute-on-read + ranked injection (~4 hrs)
    - ACT-R base-level: A_i(t) = ln(Σ_j (t - t_j)^(-d_i)) + β_i + ε
    - ε = 0 deterministic in v1 (per judge — add noise only if rich-get-richer)
    - β_i = 0 initial (Hebbian deferred to Rank 8)
    - Access events come from: created_at + supersedes (each edge = +reinforcement)
    - Force-include identity atoms (override activation threshold)
    - Diversity floor: top-k per kind (k=2)
    - Supersede suppression: atoms that are superseded do NOT appear in top-of-mind
      (they live in the archive; their supersedeers surface instead)

Integration surface: emits `top_of_mind.json` at ~/.claude/shared/atoms/.
Later, claude.py reads this and prepends to the CLAUDE.md injection stack
as a <!-- BEGIN KAI BRAIN INJECTION --> block.

Usage:
    python3 -m kai.brain.activate                  # reclassify + rank + write top_of_mind
    python3 -m kai.brain.activate --budget 50      # top 50 atoms
    python3 -m kai.brain.activate --show-top 20    # print top 20 to stdout (debug)
    python3 -m kai.brain.activate --reclassify     # only run reclassifier, don't rank
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict
from datetime import datetime, timezone, date
from pathlib import Path

HOME = Path.home()
ATOM_ROOT = HOME / ".claude" / "shared" / "atoms"
ATOM_INDEX = ATOM_ROOT / "index.jsonl"
SUPERSEDED = ATOM_ROOT / "superseded.jsonl"
TOP_OF_MIND = ATOM_ROOT / "top_of_mind.json"
ACTIVATION_CACHE = ATOM_ROOT / "activations.json"  # debug/inspection

# ─── Rank 2: 5-class temporal validity ──────────────────────────────────────

# Decay rates d. Higher d = faster decay.
# Model A's ACT-R-calibrated schedule.
DECAY_RATES = {
    "identity": 0.05,     # ~50 year half-life
    "stable": 0.15,       # ~2 years
    "semi_stable": 0.35,  # ~90 days
    "operational": 0.50,  # ~14 days (ACT-R default)
    "ephemeral": 0.80,    # ~2 days
    "expired": 2.00,      # aggressive decay for past-TTL atoms (Model B)
}

HALF_LIFE_DAYS = {
    "identity": 18250,
    "stable": 730,
    "semi_stable": 90,
    "operational": 14,
    "ephemeral": 2,
    "expired": 1,
}

# File-path rules
PATH_RULES = [
    (re.compile(r"user-identity\.md$"), "identity"),
    (re.compile(r"behavioral-debt\.(md|yaml)$"), "stable"),
    (re.compile(r"CLAUDE\.md$"), "stable"),
    (re.compile(r"KYMA-DOCTRINE\.md$"), "stable"),
    (re.compile(r"MEMORY(?:-PRIVATE)?\.md$"), "stable"),
    (re.compile(r"HACKS\.md$"), "semi_stable"),
    (re.compile(r"DECISIONS\.md$"), "semi_stable"),
    (re.compile(r"STATE\.md$"), "semi_stable"),
    (re.compile(r"TASKS\.md$"), "operational"),
    (re.compile(r"/logs/\d{4}-\d{2}-\d{2}\.md$"), "ephemeral"),
    (re.compile(r"AGENT_FEEDBACK\.md$"), "semi_stable"),
]

# Category → class (applies when log-style entry)
CATEGORY_RULES = {
    "DECISION": "semi_stable",
    "MILESTONE": "semi_stable",
    "CORRECTION": "semi_stable",
    "INSIGHT": "stable",
    "LEARNING": "stable",
    "COMPLETED": "ephemeral",
    "STARTED": "ephemeral",
    "BLOCKER": "operational",
    "STATUS": "ephemeral",
}

# Strong topic patterns — anchor atoms to more-stable class
STRONG_TOPIC_RE = re.compile(r"\b(?:MODEL-\d{3}|EXP-R\d+(?:\.\d+)?|DIAG-\d{2,}|MERT-\d+|CP-POST-\d+)\b", re.IGNORECASE)

# TTL extraction — multiple common formats
TTL_PATTERNS = [
    re.compile(r"\b(?:due|deadline|by|expires?)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(\d{4}-\d{2}-\d{2})\s+(?:deadline|due)", re.IGNORECASE),
    re.compile(r"(?:^|\s)(?:by|on)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(\d{4})", re.IGNORECASE),
]


def classify(atom: dict) -> tuple[str, str | None]:
    """Return (volatility_class, ttl_hint). Pure function; does not mutate."""
    source_file = atom.get("source_file", "")
    category = atom.get("category")
    body = atom.get("body", "")
    heading = atom.get("heading", "")
    existing_ttl = atom.get("ttl_hint")

    # Path rules first (highest priority)
    for rx, cls in PATH_RULES:
        if rx.search(source_file):
            path_class = cls
            break
    else:
        path_class = None

    # Category override for log entries
    cat_class = CATEGORY_RULES.get(category) if category else None

    # Strong topic promotion: anchor to more-stable class
    has_strong_topic = bool(STRONG_TOPIC_RE.search(heading + " " + body[:400]))

    # Resolve class
    cls = cat_class or path_class or "operational"

    # Strong topic upgrade for ephemeral operational logs that reference a stable topic
    if has_strong_topic and cls in ("ephemeral", "operational"):
        cls = "semi_stable"

    # TTL extraction
    ttl = existing_ttl
    if not ttl:
        for rx in TTL_PATTERNS:
            m = rx.search(body)
            if m:
                # If regex captured year-only, skip (needs more work); only accept YYYY-MM-DD
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", m.group(1)):
                    ttl = m.group(1)
                    break

    # TTL auto-expire: if past TTL, reclassify ephemeral (or expired if way past)
    if ttl:
        try:
            ttl_date = date.fromisoformat(ttl)
            today = date.today()
            days_past = (today - ttl_date).days
            if days_past > 0:
                if days_past > 7:
                    cls = "expired"
                else:
                    cls = "ephemeral"
        except ValueError:
            pass

    return cls, ttl


# ─── Rank 3: ACT-R activation ──────────────────────────────────────────────

# Access events for MVP come from:
#   - atom creation timestamp
#   - each supersede edge INTO this atom (meaning: it was recently updated)
#   - each supersede edge OUT FROM this atom to its superseders cluster
# Real Hebbian access logging is Rank 6/8.

def _load_atoms() -> list[dict]:
    if not ATOM_INDEX.exists():
        return []
    out = []
    for line in ATOM_INDEX.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _load_edges() -> list[dict]:
    if not SUPERSEDED.exists():
        return []
    out = []
    for line in SUPERSEDED.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _parse_iso(s: str) -> datetime:
    if not s:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def compute_activation(atom: dict, events_into: list[datetime], d: float,
                        now: datetime, eps: float = 0.0) -> float:
    """ACT-R base-level activation.

    A_i(t) = ln(Σ_j s_j · (t - t_j)^(-d)) + β_i + ε

    s_j = event strength (1.0 for creation, 0.5 for supersede-related reinforcement).
    β_i = 0 for MVP (no Hebbian).
    ε = 0 for MVP (deterministic).
    """
    created = _parse_iso(atom.get("created_at", ""))
    # Event list (all strengths 1.0 for creation; 0.5 per reinforce event)
    # Guard: (t - t_j) must be > 0. Use >= 1 second.
    def _age(t_j: datetime) -> float:
        dt_sec = (now - t_j).total_seconds()
        return max(1.0, dt_sec)

    # Convert seconds to days (ACT-R uses arbitrary time unit; days works here)
    def _age_days(t_j: datetime) -> float:
        return _age(t_j) / 86400.0

    s_creation = 1.0
    s_reinforce = 0.5

    total = 0.0
    total += s_creation * (_age_days(created) ** (-d))
    for t_j in events_into:
        total += s_reinforce * (_age_days(t_j) ** (-d))

    if total <= 0:
        return -10.0
    return math.log(total) + 0.0 + eps


# ─── Ranking ───────────────────────────────────────────────────────────────

def _log_date_from_path(path: str) -> datetime | None:
    """Extract date from .memory/logs/YYYY-MM-DD.md filename."""
    m = re.search(r"/logs/(\d{4}-\d{2}-\d{2})\.md$", path)
    if m:
        try:
            d = date.fromisoformat(m.group(1))
            return datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


# Class-based activation floor: identity and stable items get a large additive prior
# so they don't sink under ephemeral recency spikes. Semi-stable gets some prior.
# Per synthesis judge: force-include identity regardless of activation; this provides
# ordered ranking among the rest.
CLASS_PRIOR = {
    "identity":    +6.0,
    "stable":      +4.0,
    "semi_stable": +2.0,
    "operational": +0.5,
    "ephemeral":   -1.5,  # damp ephemeral unless strong evidence
    "expired":     -6.0,  # hard suppression
}


def rank_atoms(atoms: list[dict], edges: list[dict], budget: int = 50) -> list[dict]:
    """Return the top_of_mind list. Each entry contains minimal reference fields."""
    now = datetime.now(timezone.utc)

    # Superseded atom ids — these do NOT appear in top-of-mind (they are archived)
    superseded_ids = {e["superseded_atom_id"] for e in edges}

    # Reinforcement events into each atom — use the SUPERSEDER's atom date
    # (file date for logs, atom.created_at otherwise). detected_at is "now" and provides
    # no information.
    by_id = {a["atom_id"]: a for a in atoms}
    reinforcements: dict[str, list[datetime]] = {}
    for e in edges:
        superseder_id = e["superseder_atom_id"]
        superseder = by_id.get(superseder_id)
        if not superseder:
            continue
        # Best chronology source: log-file date in filename; else created_at
        ts = _log_date_from_path(superseder.get("source_file", "")) or _parse_iso(superseder.get("created_at", ""))
        reinforcements.setdefault(superseder_id, []).append(ts)

    # For each atom, the "creation time" that activation uses should also respect log-file dates.
    scored: list[tuple[float, dict, str]] = []
    for a in atoms:
        if a["atom_id"] in superseded_ids:
            continue  # filter out superseded atoms
        cls, ttl = classify(a)
        a["volatility_class"] = cls
        if ttl and not a.get("ttl_hint"):
            a["ttl_hint"] = ttl
        d = DECAY_RATES[cls]

        # Use log-file-date-derived creation if available
        file_date = _log_date_from_path(a.get("source_file", ""))
        atom_for_activation = dict(a)
        if file_date:
            atom_for_activation["created_at"] = file_date.isoformat()

        events = reinforcements.get(a["atom_id"], [])
        raw_activation = compute_activation(atom_for_activation, events, d, now)
        # Apply class prior to give identity / stable atoms their due
        activation = raw_activation + CLASS_PRIOR.get(cls, 0.0)
        scored.append((activation, a, cls))

    # Force-include identity + stable atoms (they always matter)
    pinned = [t for t in scored if t[2] in ("identity", "stable")]
    rest = [t for t in scored if t[2] not in ("identity", "stable")]
    pinned.sort(key=lambda t: t[0], reverse=True)
    rest.sort(key=lambda t: t[0], reverse=True)

    # Diversity: top-k per kind — looser cap; also cap per-file to prevent single log dominating
    from collections import Counter
    kind_counts: Counter = Counter()
    file_counts: Counter = Counter()
    kind_cap = 8
    file_cap = 5
    selected: list[tuple[float, dict, str]] = list(pinned)
    for entry in pinned:
        _, atom, _ = entry
        kind_counts[atom.get("kind", "section")] += 1
        file_counts[atom["source_file"]] += 1
    for entry in rest:
        activation, atom, cls = entry
        kind = atom.get("kind", "section")
        src = atom["source_file"]
        if kind_counts[kind] >= kind_cap:
            continue
        if file_counts[src] >= file_cap:
            continue
        selected.append(entry)
        kind_counts[kind] += 1
        file_counts[src] += 1
        if len(selected) >= budget:
            break

    selected.sort(key=lambda t: t[0], reverse=True)

    # Shape the output: only fields needed for injection
    top_of_mind = []
    for activation, atom, cls in selected:
        top_of_mind.append({
            "atom_id": atom["atom_id"],
            "activation": round(activation, 4),
            "volatility_class": cls,
            "decay_rate": DECAY_RATES[cls],
            "half_life_days": HALF_LIFE_DAYS[cls],
            "ttl_hint": atom.get("ttl_hint"),
            "source_file": atom["source_file"],
            "source_line": atom.get("source_line"),
            "heading": atom.get("heading"),
            "kind": atom.get("kind"),
            "category": atom.get("category"),
            "body_preview": (atom.get("body") or "")[:400],
            "truth_links": atom.get("truth_links") or [],
            "supersedes": atom.get("supersedes") or [],
            "extracted_entities": (atom.get("extracted_entities") or [])[:5],
        })
    return top_of_mind


# ─── CLI ───────────────────────────────────────────────────────────────────

def write_top_of_mind(entries: list[dict]) -> None:
    ATOM_ROOT.mkdir(parents=True, exist_ok=True)
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(entries),
        "decay_rates": DECAY_RATES,
        "half_life_days": HALF_LIFE_DAYS,
    }
    TOP_OF_MIND.write_text(json.dumps({"meta": meta, "top": entries}, indent=2), encoding="utf-8")


def cmd_show_top(entries: list[dict], n: int = 20) -> None:
    print(f"\n=== Top {min(n, len(entries))} atoms (activation-ranked) ===\n")
    for i, e in enumerate(entries[:n], 1):
        ttl = f" TTL={e['ttl_hint']}" if e["ttl_hint"] else ""
        sups = f" supersedes={len(e['supersedes'])}" if e["supersedes"] else ""
        trs = f" truth_links={len(e['truth_links'])}" if e["truth_links"] else ""
        print(f"{i:3d}. [{e['volatility_class']:12s}] A={e['activation']:+.3f}  {e['heading'][:70]}")
        print(f"      {e['source_file'].replace(str(Path.home()), '~')}:{e.get('source_line', '?')}{ttl}{sups}{trs}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=50, help="Top-N atoms in top_of_mind.json")
    ap.add_argument("--show-top", type=int, default=0, help="Print top N and exit")
    ap.add_argument("--reclassify-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    atoms = _load_atoms()
    edges = _load_edges()
    if not atoms:
        print("[activate] no atoms found — run `python3 -m kai.brain.atomize` first", file=sys.stderr)
        return 1

    if args.reclassify_only:
        # Re-classify atoms in-place in the index file
        reclassified = 0
        for a in atoms:
            old = a.get("volatility_class")
            new_cls, new_ttl = classify(a)
            if old != new_cls or (new_ttl and not a.get("ttl_hint")):
                a["volatility_class"] = new_cls
                if new_ttl:
                    a["ttl_hint"] = new_ttl
                reclassified += 1
        if not args.dry_run:
            ATOM_INDEX.write_text("\n".join(json.dumps(a, default=str) for a in atoms) + "\n")
        print(f"[activate] reclassified {reclassified}/{len(atoms)} atoms", file=sys.stderr)
        return 0

    entries = rank_atoms(atoms, edges, budget=args.budget)

    if args.show_top:
        cmd_show_top(entries, args.show_top)
        return 0

    if not args.dry_run:
        write_top_of_mind(entries)
    print(f"[activate] atoms={len(atoms)}  edges={len(edges)}  top_of_mind={len(entries)}", file=sys.stderr)
    print(f"[activate] wrote {TOP_OF_MIND}", file=sys.stderr)
    from collections import Counter
    by_cls = Counter(e["volatility_class"] for e in entries)
    print("\n[activate] top-of-mind by class:", file=sys.stderr)
    for cls, c in by_cls.most_common():
        print(f"  {cls}: {c}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
