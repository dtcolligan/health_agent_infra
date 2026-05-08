"""W-AI-2 (v0.1.17 §2.D) — `hai eval review` triage state.

Persists per-scenario triage (tag / dismiss / note) so an operator can
walk the evaluation corpus across sessions without redoing analysis.

OQ-2 ratification: persistence path is the user's local state dir
(``~/.local/share/health_agent_infra/eval_review.json``), per Codex
round-1 opinion ("agent-safe per-user triage; a packaged data dir
would be wrong for mutable state").

Schema:
    {
      "schema_version": "eval_review.v1",
      "entries": {
        "<scenario_id>": {
          "scenario_id": str,
          "state": "tagged" | "dismissed",
          "tag": str | None,
          "note": str | None,
          "reason": str | None,           # only when dismissed
          "updated_at": ISO8601,
        },
        ...
      }
    }

This is a separate persistence layer from ``evals/scenarios/`` (the
fixture tree, packaged with the wheel). The fixture tree is read-only
substrate; the review state is mutable per-user triage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


SCHEMA_VERSION = "eval_review.v1"


def default_state_path() -> Path:
    """Default persistence path. Overridable via ``HAI_EVAL_REVIEW_STATE``."""

    import os
    override = os.environ.get("HAI_EVAL_REVIEW_STATE")
    if override:
        return Path(override).expanduser()
    return (
        Path.home() / ".local" / "share" / "health_agent_infra" /
        "eval_review.json"
    )


@dataclass(frozen=True)
class ReviewEntry:
    """One per-scenario triage entry."""

    scenario_id: str
    state: str                     # "tagged" | "dismissed"
    tag: Optional[str]
    note: Optional[str]
    reason: Optional[str]
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "state": self.state,
            "tag": self.tag,
            "note": self.note,
            "reason": self.reason,
            "updated_at": self.updated_at,
        }


def load_state(path: Optional[Path] = None) -> dict[str, Any]:
    """Load the review state file. Returns the v1 empty shape if absent."""

    target = path or default_state_path()
    if not target.exists():
        return {"schema_version": SCHEMA_VERSION, "entries": {}}
    raw = json.loads(target.read_text(encoding="utf-8"))
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"unrecognised schema_version {raw.get('schema_version')!r} "
            f"in {target}; expected {SCHEMA_VERSION}"
        )
    return raw


def save_state(state: dict[str, Any], path: Optional[Path] = None) -> Path:
    """Persist the review state. Creates the parent dir if needed."""

    target = path or default_state_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def tag_scenario(
    scenario_id: str,
    *,
    tag: str,
    note: Optional[str] = None,
    path: Optional[Path] = None,
) -> ReviewEntry:
    """Set a triage tag on a scenario. Replaces any prior entry."""

    state = load_state(path)
    now = datetime.now(timezone.utc).isoformat()
    entry = ReviewEntry(
        scenario_id=scenario_id,
        state="tagged",
        tag=tag,
        note=note,
        reason=None,
        updated_at=now,
    )
    state["entries"][scenario_id] = entry.to_dict()
    save_state(state, path)
    return entry


def dismiss_scenario(
    scenario_id: str,
    *,
    reason: str,
    path: Optional[Path] = None,
) -> ReviewEntry:
    """Mark a scenario dismissed with a free-text reason."""

    state = load_state(path)
    now = datetime.now(timezone.utc).isoformat()
    entry = ReviewEntry(
        scenario_id=scenario_id,
        state="dismissed",
        tag=None,
        note=None,
        reason=reason,
        updated_at=now,
    )
    state["entries"][scenario_id] = entry.to_dict()
    save_state(state, path)
    return entry


def list_corpus(
    *,
    corpus: str = "all",
    tag_filter: Optional[str] = None,
    include_dismissed: bool = False,
    path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Walk the live corpus + overlay triage state.

    ``corpus`` is one of ``"scenarios"`` (the per-domain + synthesis
    fixture tree), ``"judge_adversarial"`` (the W-AI judge corpus), or
    ``"all"`` (both). The fixture tree is the substrate of truth; the
    triage state from ``eval_review.json`` overlays per-scenario
    ``state`` / ``tag`` / ``note`` / ``reason`` fields.

    ``tag_filter`` narrows to entries already carrying that tag in
    triage state. ``include_dismissed=False`` (default) hides dismissed
    rows from the listing.

    Returns a list of dicts sorted by scenario_id.
    """

    state = load_state(path)
    entries = state["entries"]

    rows: list[dict[str, Any]] = []
    for scenario in _walk_corpus(corpus):
        sid = scenario["scenario_id"]
        triage = entries.get(sid, {})
        if not include_dismissed and triage.get("state") == "dismissed":
            continue
        if tag_filter is not None and triage.get("tag") != tag_filter:
            continue
        rows.append({
            "scenario_id": sid,
            "kind": scenario.get("kind"),
            "domain": scenario.get("domain"),
            "tag_in_fixture": scenario.get("tag"),
            "triage_state": triage.get("state"),
            "triage_tag": triage.get("tag"),
            "triage_note": triage.get("note"),
            "triage_reason": triage.get("reason"),
            "triage_updated_at": triage.get("updated_at"),
        })
    rows.sort(key=lambda r: r["scenario_id"])
    return rows


def show_scenario(
    scenario_id: str,
    *,
    path: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    """Return one scenario's fixture body + any triage overlay, or None."""

    fixture = _find_in_corpus(scenario_id)
    if fixture is None:
        return None
    state = load_state(path)
    triage = state["entries"].get(scenario_id)
    return {"fixture": fixture, "triage": triage}


def export_state(
    *,
    output: Path,
    fmt: str = "json",
    path: Optional[Path] = None,
) -> Path:
    """Export the full triage state to a file. ``fmt`` is ``json`` or
    ``csv``."""

    state = load_state(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        output.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    elif fmt == "csv":
        import csv as _csv
        with output.open("w", encoding="utf-8", newline="") as fh:
            writer = _csv.DictWriter(
                fh,
                fieldnames=[
                    "scenario_id", "state", "tag", "note", "reason",
                    "updated_at",
                ],
            )
            writer.writeheader()
            for entry in sorted(
                state["entries"].values(),
                key=lambda e: e["scenario_id"],
            ):
                writer.writerow(entry)
    else:
        raise ValueError(f"unknown export format: {fmt!r}")
    return output


# ---------------------------------------------------------------------------
# Internal — corpus walker (reads fixture tree from package data)
# ---------------------------------------------------------------------------


_NON_DOMAIN_SCENARIO_DIRS: frozenset[str] = frozenset({
    # judge_adversarial is walked separately below — its fixtures are
    # keyed by ``fixture_id`` and live in per-category subdirectories.
    "judge_adversarial",
    # atomic_claims (v0.2.0 W-FACT-ATOM) is a parser-precision corpus
    # whose fixtures are markdown + ground-truth atom triples, not
    # review-listable scenarios. They have no ``scenario_id`` field.
    "atomic_claims",
    # factuality (v0.2.0 W58D) is the deterministic factuality-gate
    # corpus — known-bad and known-good ClaimGateInput payloads keyed
    # by ``fixture_id``. Not review-listable as domain scenarios.
    "factuality",
})


def _walk_corpus(corpus: str) -> list[dict[str, Any]]:
    """Walk the fixture tree and return per-scenario summary dicts.

    Pulled from ``evals/scenarios/`` directly via importlib.resources;
    the fixture tree ships in the wheel as package_data.
    """

    if corpus not in ("all", "scenarios", "judge_adversarial"):
        raise ValueError(f"unknown corpus: {corpus!r}")

    out: list[dict[str, Any]] = []
    base = Path(__file__).parent / "scenarios"

    if corpus in ("scenarios", "all"):
        for domain_dir in sorted(base.iterdir()):
            if (
                not domain_dir.is_dir()
                or domain_dir.name in _NON_DOMAIN_SCENARIO_DIRS
            ):
                continue
            for fixture_path in sorted(domain_dir.glob("*.json")):
                if fixture_path.name == "index.json":
                    continue
                fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
                out.append({
                    "scenario_id": fixture.get("scenario_id"),
                    "kind": fixture.get("kind", "domain"),
                    "domain": fixture.get("domain", domain_dir.name),
                    "tag": fixture.get("tag"),
                    "_path": str(fixture_path.relative_to(base)),
                })

    if corpus in ("judge_adversarial", "all"):
        ja_dir = base / "judge_adversarial"
        if ja_dir.exists():
            for sub_dir in sorted(ja_dir.iterdir()):
                if not sub_dir.is_dir():
                    continue
                for fixture_path in sorted(sub_dir.glob("*.json")):
                    if fixture_path.name == "index.json":
                        continue
                    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
                    out.append({
                        "scenario_id": fixture.get("scenario_id") or fixture_path.stem,
                        "kind": "judge_adversarial",
                        "domain": sub_dir.name,
                        "tag": fixture.get("tag"),
                        "_path": str(fixture_path.relative_to(base)),
                    })

    return out


def _find_in_corpus(scenario_id: str) -> Optional[dict[str, Any]]:
    """Find a single scenario's full fixture body anywhere in the tree.

    Id contract matches :func:`_walk_corpus`: a fixture is selectable by
    its ``scenario_id`` (domain corpus convention), its ``fixture_id``
    (judge_adversarial convention), or its file stem (last-resort
    fallback for fixtures that carry neither).
    """

    base = Path(__file__).parent / "scenarios"
    for fixture_path in base.rglob("*.json"):
        if fixture_path.name == "index.json":
            continue
        try:
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        candidate_ids = (
            fixture.get("scenario_id"),
            fixture.get("fixture_id"),
            fixture_path.stem,
        )
        if scenario_id in candidate_ids:
            return fixture
    return None
