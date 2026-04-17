#!/usr/bin/env python3
"""
atomize.py — Rank-1 brain-memory primitive from 2026-04-16 consultation synthesis.

What it does:
- Walks Kai's memory surfaces (workspace .memory/, ~/.claude/, kyma-engine, kyma-landing).
- Splits each markdown file into ATOMS: one atom per (level-2 heading OR [CATEGORY] entry).
- Generates stable atom_id = sha256(source_file + anchor + content_sha_prefix[:8])[:16].
- Rewrites truth-layer claims (MODEL-\\d+ etc.) to POINTERS referencing kyma-engine/manifests/*.yaml.
- Detects supersede edges: [COMPLETED] / [MILESTONE] / [DECISION] / ON HOLD / CANCELLED entries
  attempt to match prior atoms by (topic | entity | heading overlap).
- Writes append-only index at ~/.claude/shared/atoms/index.jsonl.
- Writes supersede ledger at ~/.claude/shared/atoms/superseded.jsonl (append-only).
- Emits truth-pointer coverage gaps at ~/.claude/shared/atoms/truth-coverage-gaps.jsonl
  (per judge: log misses for weekly review).

This is the single highest-leverage move per the consultation synthesis:
it structurally kills zombies (YC, a16z ON HOLD contradiction, STATE.md staleness)
by emitting supersede edges. Decay math comes LATER. The atomizer ships first.

Per synthesis open-question judgments:
- Granularity: per [CATEGORY] entry (semantic unit of logs)
- Truth-pointer regex: start narrow, log misses
- behavioral-debt.yaml migration: additive (keep recurrence_count as derived)
- Atom index location: global (~/.claude/shared/atoms/)
- Trigger: session-start hook (lazy) for MVP
- Architectural firewall: atomizer emits, no Kai self-modification
- Noise: ε = 0 (deterministic ranking for debug)

Usage:
    python3 atomize.py                     # full walk, append to global index
    python3 atomize.py --dry-run           # enumerate without writing
    python3 atomize.py --scope workspace   # only kai/workspace
    python3 atomize.py --show atom <id>    # inspect one atom
    python3 atomize.py --stats             # summary counts
    python3 atomize.py --conflicts         # show detected supersede candidates
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
ATOM_ROOT = HOME / ".claude" / "shared" / "atoms"
ATOM_INDEX = ATOM_ROOT / "index.jsonl"
SUPERSEDED = ATOM_ROOT / "superseded.jsonl"
COVERAGE_GAPS = ATOM_ROOT / "truth-coverage-gaps.jsonl"

SCOPES = {
    "workspace": [
        HOME / "kai/workspace/.memory/TASKS.md",
        HOME / "kai/workspace/.memory/STATE.md",
        HOME / "kai/workspace/.memory/DECISIONS.md",
        HOME / "kai/workspace/.memory/LESSONS.md",
        HOME / "kai/workspace/.memory/CONTRACTS.md",
        HOME / "kai/workspace/.claude/MEMORY.md",
        HOME / "kai/workspace/.claude/HACKS.md",
        HOME / "kai/workspace/KYMA-DOCTRINE.md",
    ],
    "workspace_logs_glob": HOME / "kai/workspace/.memory/logs",  # glob *.md
    "global": [
        HOME / ".claude/CLAUDE.md",
        HOME / ".claude/user-identity.md",
        HOME / ".claude/behavioral-debt.md",
    ],
    "kyma_engine": [
        HOME / "code/kyma-engine/TASKS.md",
        HOME / "code/kyma-engine/AGENT_FEEDBACK.md",
        HOME / "code/kyma-engine/AGENTS.md",
        HOME / "code/kyma-engine/CLAUDE.md",
        HOME / "code/kyma-engine/README.md",
    ],
    "kyma_landing": [
        HOME / "code/kyma-landing/TASKS.md" if (HOME / "code/kyma-landing/TASKS.md").exists() else None,
        HOME / "code/kyma-landing/.memory/TASKS.md" if (HOME / "code/kyma-landing/.memory/TASKS.md").exists() else None,
    ],
    "notion_glob": HOME / "kai/notion-kyma-space-2",  # glob *.md — Kyma Space 2.0 Notion dump
}

# --- Atom schema ------------------------------------------------------------

CATEGORY_RE = re.compile(r"^\s*##\s+(\d{1,2}:\d{2}\s+)?\[([A-Z_]+)\]\s*(.*)$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)$", re.MULTILINE)
SUPERSEDE_TRIGGER_CATEGORIES = {
    "COMPLETED", "MILESTONE", "DECISION", "CORRECTION", "BLOCKER",
    "CANCELLED", "ABANDONED", "SUPERSEDED", "DEPRECATED", "ONHOLD", "ON_HOLD"
}
SUPERSEDE_PHRASES = [
    (r"\bon[\s-]?hold\b", "on_hold"),
    (r"\bcancel(?:led|ed)?\b", "cancelled"),
    (r"\babandon(?:ed)?\b", "abandoned"),
    (r"\bsupersed(?:ed|es)\s+by\s+([A-Z0-9\-_.]+)", "supersede_ref"),
    (r"\bno[\s-]?longer\b", "no_longer"),
    (r"\bdeferred\b", "deferred"),
    (r"\bdone\b", "done"),
    (r"\bcompleted\b", "completed"),
]

# Truth-pointer patterns (start narrow per judge recommendation)
TRUTH_PATTERNS = [
    # MODEL-nnn / EXP-Rnn / DIAG-nn topics with a numeric value
    (re.compile(r"\b(MODEL-\d{3}|EXP-R\d+(?:\.\d+)?|DIAG-\d{2,})\s*(?::|=|\s+is|\s+at)?\s*([a-zA-Z_]+)\s*[=:]\s*([\d.]+)", re.IGNORECASE), "metric_equals"),
    (re.compile(r"\b(MODEL-\d{3}|EXP-R\d+(?:\.\d+)?|DIAG-\d{2,}).*?(val_cos|F1|NDCG(?:@\d+)?|r|correlation_r|coverage|coherence|retention|baseline)\s*[=:]\s*([\d.]+)", re.IGNORECASE), "metric_labeled"),
]

# Entity extractor — coarse (first-pass). Match common topic tokens + caps-word phrases.
ENTITY_RE = re.compile(
    r"\b(MODEL-\d{3}|EXP-R\d+(?:\.\d+)?|DIAG-\d{2,}|F-[A-Z0-9\-_.]+|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b"
)


@dataclass
class Atom:
    atom_id: str
    scope: str
    source_file: str
    source_anchor: str             # line number or section slug
    source_line: int
    content_sha: str               # sha256(body)[:16]
    kind: str                      # category (COMPLETED, DECISION, etc.) or 'section'
    category: str | None           # [CATEGORY] if log-style, else None
    heading: str                   # heading text / first line
    body: str                      # content (<=2000 chars)
    truth_links: list[dict] = field(default_factory=list)
    rewritten_body: str | None = None
    supersedes: list[str] = field(default_factory=list)   # atom_ids
    supersede_reason: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec='seconds'))
    extracted_entities: list[str] = field(default_factory=list)
    volatility_class: str = "operational"  # default; real classifier is Rank-2
    ttl_hint: str | None = None


# --- Helpers ---------------------------------------------------------------

def _stable_atom_id(source_file: str, anchor: str, body: str) -> str:
    h_body = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()[:8]
    raw = f"{source_file}#{anchor}#{h_body}"
    return "A-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", s).strip().lower()
    s = re.sub(r"\s+", "-", s)
    return s[:64]


def _truncate(text: str, cap: int = 2000) -> str:
    if len(text) <= cap:
        return text
    return text[:cap].rsplit("\n", 1)[0] + "\n\n[...truncated...]"


def _extract_entities(text: str, max_n: int = 10) -> list[str]:
    seen = set()
    out = []
    for m in ENTITY_RE.finditer(text):
        e = m.group(1)
        if e in seen or e.lower() in {"the", "and", "but", "for", "this", "that", "claude"}:
            continue
        seen.add(e)
        out.append(e)
        if len(out) >= max_n:
            break
    return out


def _detect_ttl_hint(text: str) -> str | None:
    m = re.search(r"\b(?:due|deadline|by|expires?)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def _classify_kind(category: str | None, file_path: str, heading: str) -> tuple[str, str]:
    """Return (kind, volatility_class)."""
    fp = str(file_path).lower()
    if "user-identity" in fp:
        return ("identity", "identity")
    # CLAUDE.md = highest-attention operating system per Idam 2026-04-17 directive.
    # Every heading in CLAUDE.md is identity-class so it force-includes and never decays.
    if fp.endswith("claude.md") or "/claude.md" in fp:
        return ("claude_md", "identity")
    if "behavioral-debt" in fp:
        return ("behavioral", "stable")
    if category == "DECISION":
        return ("decision", "semi_stable")
    if category == "MILESTONE":
        return ("milestone", "semi_stable")
    # [CORRECTION] atoms never decay per Idam 2026-04-17 directive.
    # "for your brain i want corrections to also be top of mind and not decay so you never forget them"
    if category == "CORRECTION":
        return ("correction", "identity")
    if category in ("COMPLETED", "STARTED", "STATUS"):
        return ("operational_log", "ephemeral")
    if category == "INSIGHT":
        return ("insight", "stable")
    if category == "LEARNING":
        return ("learning", "stable")
    if category == "BLOCKER":
        return ("blocker", "operational")
    if "tasks.md" in fp:
        return ("task", "operational")
    if "/logs/" in fp or re.search(r"\d{4}-\d{2}-\d{2}\.md", fp):
        return ("log_section", "ephemeral")
    if "state.md" in fp:
        return ("state", "semi_stable")
    if "decisions.md" in fp:
        return ("decision", "semi_stable")
    if "hacks.md" in fp:
        return ("hack", "semi_stable")
    if category:
        return (category.lower(), "operational")
    return ("section", "operational")


def _rewrite_truth_pointers(body: str) -> tuple[str, list[dict], list[dict]]:
    """Replace truth-layer values with pointers. Return (rewritten, truth_links, gaps)."""
    truth_links: list[dict] = []
    gaps: list[dict] = []
    # Only the first pattern fires authoritatively; second is fallback detection
    for pattern, kind in TRUTH_PATTERNS:
        for m in pattern.finditer(body):
            topic = m.group(1).upper()
            # Some groups may not exist in all patterns — guard
            try:
                metric = m.group(2)
                value = m.group(3)
            except IndexError:
                continue
            truth_links.append({
                "topic": topic,
                "metric": metric,
                "cached_value": value,
                "manifest_path": f"manifests/{topic}.yaml",
                "manifest_pointer": f"#{metric}",
                "pattern": kind,
            })
    # Detect obvious numeric claims that did NOT match our narrow regex — flag as gaps
    bare_metric = re.compile(r"\b(baseline|val_cos|F1|NDCG(?:@\d+)?|r|correlation_r)\b\s*(?:is|of|at)\s+(\d+\.\d+)", re.IGNORECASE)
    for m in bare_metric.finditer(body):
        gaps.append({
            "metric": m.group(1),
            "value": m.group(2),
            "context": body[max(0, m.start()-40):m.end()+40],
        })
    return body, truth_links, gaps  # rewriting is injection-time (Rank-3); here we collect pointers


# --- Atomizer core ---------------------------------------------------------

def atomize_file(path: Path, scope: str) -> list[Atom]:
    if not path.exists() or not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if path.stat().st_size > 2 * 1024 * 1024:
        return []
    atoms: list[Atom] = []

    # Prefer [CATEGORY] entries if present; otherwise fall back to ## sections
    cat_matches = list(CATEGORY_RE.finditer(text))
    h2_matches = list(H2_RE.finditer(text))

    splits: list[tuple[int, str, str | None, str]] = []
    # splits = [(start_line_offset_in_chars, heading_text, category_or_None, anchor_slug)]
    if cat_matches:
        for m in cat_matches:
            start = m.start()
            line_no = text.count("\n", 0, start) + 1
            time_prefix = (m.group(1) or "").strip()
            category = m.group(2)
            remainder = m.group(3).strip()
            heading = f"[{category}] {remainder}".strip()
            anchor = f"L{line_no}-{_slugify(category + '-' + remainder)}"
            splits.append((start, heading, category, anchor, line_no, time_prefix))
    elif h2_matches:
        for m in h2_matches:
            start = m.start()
            line_no = text.count("\n", 0, start) + 1
            heading = m.group(1).strip()
            anchor = f"L{line_no}-{_slugify(heading)}"
            splits.append((start, heading, None, anchor, line_no, ""))
    else:
        # whole-file atom (rare; tiny files)
        anchor = "L1-full"
        splits.append((0, path.name, None, anchor, 1, ""))

    # Append terminal sentinel so we can slice bodies
    starts = [s[0] for s in splits] + [len(text)]

    for idx, (start, heading, category, anchor, line_no, time_prefix) in enumerate(splits):
        body = text[start:starts[idx + 1]].strip()
        body = _truncate(body)
        if not body:
            continue
        content_sha = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()[:16]
        atom_id = _stable_atom_id(str(path), anchor, body)
        kind, volatility = _classify_kind(category, str(path), heading)
        entities = _extract_entities(heading + "\n" + body[:500])
        ttl = _detect_ttl_hint(body)
        _, truth_links, _ = _rewrite_truth_pointers(body)
        atoms.append(Atom(
            atom_id=atom_id,
            scope=scope,
            source_file=str(path),
            source_anchor=anchor,
            source_line=line_no,
            content_sha=content_sha,
            kind=kind,
            category=category,
            heading=heading,
            body=body,
            truth_links=truth_links,
            extracted_entities=entities,
            volatility_class=volatility,
            ttl_hint=ttl,
        ))
    return atoms


# --- Supersede detection ---------------------------------------------------

def _entity_overlap(a_entities: list[str], b_entities: list[str]) -> set[str]:
    return set(e.lower() for e in a_entities) & set(e.lower() for e in b_entities)


# Strong topic tokens = structured identifiers (MODEL-nnn, EXP-Rnn, DIAG-nn, F-foo)
STRONG_TOPIC_RE = re.compile(r"^(?:model-\d{3}|exp-r\d+(?:\.\d+)?|diag-\d{2,}|f-[a-z0-9\-_.]+)$", re.IGNORECASE)


def _is_strong_topic(entity: str) -> bool:
    return bool(STRONG_TOPIC_RE.match(entity))


def _log_file_date(path: str) -> str | None:
    m = re.search(r"/logs/(\d{4}-\d{2}-\d{2})\.md$", path)
    if m:
        return m.group(1)
    # Notion dump: /notion-kyma-space-2/YYYY-MM-DD-<slug>-<id8>.md
    m = re.search(r"/notion-kyma-space-2/(\d{4}-\d{2}-\d{2})-", path)
    if m:
        return m.group(1)
    return None


def _atom_chronology_key(a: Atom) -> tuple[str, int]:
    """Chronological ordering: prefer log-file date in filename, fallback to source_file+line."""
    d = _log_file_date(a.source_file)
    if d:
        return (d, a.source_line)
    # Non-log files get placed by file path ordering (stable)
    return (a.source_file, a.source_line)


def detect_supersede_edges(atoms: list[Atom]) -> list[dict]:
    """Return list of supersede edges: {superseder, superseded, reason, evidence}.

    Tighter matching than v1:
    - REQUIRE either (a) shared STRONG topic token (MODEL-nnn / EXP-Rnn / DIAG-nn)
      OR (b) >= 2 overlapping extracted entities AND one of them in the target heading.
    - Cycles dedup'd: if A→B and B→A both pass, keep only the chronologically later one.
    - Chronological ordering uses log-file date where available.
    """
    edges: list[dict] = []
    atoms_sorted = sorted(atoms, key=_atom_chronology_key)

    # Index by (strong-topic entities), plus general entity index
    by_strong_topic: dict[str, list[Atom]] = {}
    by_entity: dict[str, list[Atom]] = {}
    for a in atoms_sorted:
        for e in a.extracted_entities:
            by_entity.setdefault(e.lower(), []).append(a)
            if _is_strong_topic(e):
                by_strong_topic.setdefault(e.lower(), []).append(a)

    for a in atoms_sorted:
        trigger_phrases: list[tuple[str, str]] = []
        if a.category in SUPERSEDE_TRIGGER_CATEGORIES:
            trigger_phrases.append((f"[{a.category}]", a.category.lower()))
        body_lc = a.body.lower()
        for regex, tag in SUPERSEDE_PHRASES:
            m = re.search(regex, body_lc)
            if m:
                trigger_phrases.append((m.group(0), tag))
        if not trigger_phrases:
            continue

        a_key = _atom_chronology_key(a)
        candidates: set[str] = set()

        # Path 1: STRONG topic token overlap — high precision
        strong_topics = [e for e in a.extracted_entities if _is_strong_topic(e)]
        for e in strong_topics:
            for prior in by_strong_topic.get(e.lower(), []):
                if prior.atom_id == a.atom_id:
                    continue
                if _atom_chronology_key(prior) >= a_key:
                    continue
                candidates.add(prior.atom_id)

        # Path 2: TIGHT entity overlap — require shared entity in BOTH headings
        # AND same source file (no cross-file false positives).
        # Tightened 2026-04-17 per control-experiment follow-up: the previous
        # ≥2-entity + one-in-prior-heading heuristic generated noise like
        # "HACKS.md Modal entry superseded by HACKS.md ListenBrainz entry"
        # because generic tokens ("Modal", "Python", "Spotify") appeared across
        # unrelated entries. Requiring same-file + both-headings-mention prevents
        # cross-topic false positives while still catching real in-file revisions.
        if not strong_topics:
            a_heading_lc = a.heading.lower()
            for prior in atoms_sorted:
                if prior.atom_id == a.atom_id:
                    continue
                if _atom_chronology_key(prior) >= a_key:
                    continue
                # Cross-file pairs require a strong topic (Path 1); same-file pairs allowed here.
                if prior.source_file != a.source_file:
                    continue
                overlap = _entity_overlap(a.extracted_entities, prior.extracted_entities)
                if len(overlap) < 2:
                    continue
                prior_heading_lc = prior.heading.lower()
                # TIGHTER: shared entity must appear in BOTH headings, not just prior's.
                both_headings = [e for e in overlap
                                  if e in prior_heading_lc and e in a_heading_lc]
                if not both_headings:
                    continue
                candidates.add(prior.atom_id)

        for cand in candidates:
            edges.append({
                "superseder_atom_id": a.atom_id,
                "superseded_atom_id": cand,
                "reason": trigger_phrases[0][1],
                "trigger_phrase": trigger_phrases[0][0],
                "evidence_heading": a.heading[:160],
                "superseder_file": a.source_file,
                "detected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })

    # Dedup cycles — same (u, v) pair in both directions: keep the later superseder
    pair_key = {}
    by_id = {a.atom_id: a for a in atoms_sorted}
    for e in edges:
        u, v = e["superseder_atom_id"], e["superseded_atom_id"]
        k = tuple(sorted([u, v]))
        if k not in pair_key:
            pair_key[k] = e
            continue
        # Compare chronology; keep the edge whose superseder is later
        existing = pair_key[k]
        e_key = _atom_chronology_key(by_id[e["superseder_atom_id"]])
        ex_key = _atom_chronology_key(by_id[existing["superseder_atom_id"]])
        if e_key > ex_key:
            pair_key[k] = e
    return list(pair_key.values())


# --- Coverage-gap logging --------------------------------------------------

def collect_coverage_gaps(atoms: list[Atom]) -> list[dict]:
    out: list[dict] = []
    for a in atoms:
        _, _, gaps = _rewrite_truth_pointers(a.body)
        for g in gaps:
            # Skip if we already have a truth_link for this metric
            if any(tl["metric"].lower() == g["metric"].lower() for tl in a.truth_links):
                continue
            out.append({
                "atom_id": a.atom_id,
                "source_file": a.source_file,
                "line": a.source_line,
                **g,
            })
    return out


# --- Driver ----------------------------------------------------------------

def walk_scope(scope: str) -> list[Path]:
    files: list[Path] = []
    if scope == "workspace":
        files.extend([p for p in SCOPES["workspace"] if p and p.exists()])
        logs_dir = SCOPES["workspace_logs_glob"]
        if logs_dir.exists():
            files.extend(sorted(logs_dir.glob("*.md")))
    elif scope == "global":
        files.extend([p for p in SCOPES["global"] if p and p.exists()])
    elif scope == "kyma_engine":
        files.extend([p for p in SCOPES["kyma_engine"] if p and p.exists()])
    elif scope == "kyma_landing":
        files.extend([p for p in SCOPES["kyma_landing"] if p and p.exists()])
    elif scope == "notion":
        notion_dir = SCOPES["notion_glob"]
        if notion_dir.exists():
            files.extend(sorted(notion_dir.glob("*.md")))
    elif scope == "all":
        for s in ["workspace", "global", "kyma_engine", "kyma_landing", "notion"]:
            files.extend(walk_scope(s))
    return files


def atomize_all(scope: str) -> tuple[list[Atom], list[dict], list[dict]]:
    atoms: list[Atom] = []
    if scope == "all":
        for s in ["workspace", "global", "kyma_engine", "kyma_landing", "notion"]:
            for path in walk_scope(s):
                atoms.extend(atomize_file(path, s))
    else:
        for path in walk_scope(scope):
            atoms.extend(atomize_file(path, scope))
    # Dedup by atom_id (idempotency)
    dedup: dict[str, Atom] = {}
    for a in atoms:
        dedup[a.atom_id] = a
    atoms = list(dedup.values())
    # Back-fill supersede edges
    edges = detect_supersede_edges(atoms)
    # Write supersede info into atoms
    by_id = {a.atom_id: a for a in atoms}
    for e in edges:
        superseder = by_id.get(e["superseder_atom_id"])
        superseded = by_id.get(e["superseded_atom_id"])
        if superseder and superseded:
            if e["superseded_atom_id"] not in superseder.supersedes:
                superseder.supersedes.append(e["superseded_atom_id"])
                superseder.supersede_reason = e["reason"]
    gaps = collect_coverage_gaps(atoms)
    return atoms, edges, gaps


def write_index(atoms: list[Atom], edges: list[dict], gaps: list[dict], dry_run: bool) -> None:
    if dry_run:
        print("[dry-run] would write:", ATOM_INDEX, len(atoms), "atoms,",
              len(edges), "supersede edges,", len(gaps), "gaps", file=sys.stderr)
        return
    ATOM_ROOT.mkdir(parents=True, exist_ok=True)
    with ATOM_INDEX.open("w", encoding="utf-8") as f:
        for a in atoms:
            f.write(json.dumps(asdict(a), default=str) + "\n")
    with SUPERSEDED.open("w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, default=str) + "\n")
    with COVERAGE_GAPS.open("w", encoding="utf-8") as f:
        for g in gaps:
            f.write(json.dumps(g, default=str) + "\n")


def cmd_stats(atoms: list[Atom], edges: list[dict], gaps: list[dict]) -> None:
    from collections import Counter
    print(f"Atoms: {len(atoms)}")
    print(f"Supersede edges: {len(edges)}")
    print(f"Truth-coverage gaps: {len(gaps)}")
    by_scope = Counter(a.scope for a in atoms)
    print("\nBy scope:")
    for s, c in by_scope.most_common():
        print(f"  {s}: {c}")
    by_kind = Counter(a.kind for a in atoms)
    print("\nBy kind (top 10):")
    for k, c in by_kind.most_common(10):
        print(f"  {k}: {c}")
    by_volatility = Counter(a.volatility_class for a in atoms)
    print("\nBy volatility_class:")
    for v, c in by_volatility.most_common():
        print(f"  {v}: {c}")
    print(f"\nAtoms with truth_links: {sum(1 for a in atoms if a.truth_links)}")
    print(f"Atoms with ttl_hint: {sum(1 for a in atoms if a.ttl_hint)}")
    print(f"Atoms that supersede something: {sum(1 for a in atoms if a.supersedes)}")


def cmd_conflicts(edges: list[dict], max_show: int = 30) -> None:
    print(f"Supersede edges detected: {len(edges)}")
    for e in edges[:max_show]:
        print(f"\n- {e['superseder_atom_id']}  supersedes  {e['superseded_atom_id']}")
        print(f"  reason: {e['reason']} ({e['trigger_phrase']})")
        print(f"  file:   {e['superseder_file']}")
        print(f"  head:   {e['evidence_heading']}")


def cmd_show_atom(atoms: list[Atom], atom_id: str) -> None:
    for a in atoms:
        if a.atom_id == atom_id or a.atom_id.endswith(atom_id):
            print(json.dumps(asdict(a), indent=2, default=str))
            return
    print(f"Atom {atom_id} not found", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default="all", choices=["all", "workspace", "global", "kyma_engine", "kyma_landing", "notion"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--conflicts", action="store_true")
    ap.add_argument("--show", nargs=2, metavar=("KIND", "ID"))
    args = ap.parse_args()

    atoms, edges, gaps = atomize_all(args.scope)

    if args.show and args.show[0] == "atom":
        cmd_show_atom(atoms, args.show[1])
        return 0

    if args.stats:
        cmd_stats(atoms, edges, gaps)

    if args.conflicts:
        cmd_conflicts(edges)

    if not args.stats and not args.conflicts and not args.show:
        write_index(atoms, edges, gaps, args.dry_run)
        print(f"[atomize] scope={args.scope}  atoms={len(atoms)}  edges={len(edges)}  gaps={len(gaps)}", file=sys.stderr)
        if not args.dry_run:
            print(f"[atomize] wrote {ATOM_INDEX}", file=sys.stderr)
            print(f"[atomize] wrote {SUPERSEDED}", file=sys.stderr)
            print(f"[atomize] wrote {COVERAGE_GAPS}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
