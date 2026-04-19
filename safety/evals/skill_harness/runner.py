"""Phase E skill-harness pilot runner.

Invokes a real skill path end-to-end (recovery-readiness) and scores the
emitted ``TrainingRecommendation`` along two explicitly separated axis
groups:

1. **Deterministic correctness** — mechanical pass/fail checks over the
   structured recommendation (schema validates, ``action`` matches
   expected, confidence within bound, ``policy_decisions`` echoed
   verbatim, follow-up window honoured).
2. **Rationale quality** — a rubric-scored check over the skill-authored
   prose. This pilot scores by token presence (expected band names,
   required / forbidden uncertainty tokens). The rubric doc reserves a
   future LLM-judge slot; see ``rubrics/recovery.md``.

Three execution backends are supported:

- ``--mode live`` — invoke Claude Code as a subprocess
  (``claude --print --output-format json``) with the recovery-readiness
  SKILL.md as the system prompt and the scenario snapshot as input.
  Requires ``claude`` on PATH and ``HAI_SKILL_HARNESS_LIVE=1``. The
  emitted recommendation is written to
  ``scenarios/recovery/transcripts/<scenario_id>/<iso-stamp>.json`` so a
  later ``--mode replay`` can reproduce scoring deterministically.
- ``--mode replay`` — load the most recent transcript per scenario from
  the transcripts tree. Deterministic. This is what the pytest shim
  drives.
- ``--mode demo`` — no skill invocation; prints the composed snapshot +
  rubric expectations so a developer can hand-run the skill in Claude
  Code and paste the response back.

Opt-in by design. No CI path depends on live invocation. See
``safety/evals/skill_harness_blocker.md`` for what the pilot resolves
versus what remains out of scope.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


HARNESS_ROOT = Path(__file__).resolve().parent
SCENARIOS_ROOT = HARNESS_ROOT / "scenarios"
RUBRICS_ROOT = HARNESS_ROOT / "rubrics"

SUPPORTED_DOMAINS = ("recovery",)


class HarnessError(RuntimeError):
    """Raised on harness-level problems (scenario malformed, live-mode
    unavailable, transcript missing) rather than scorer failures."""


# ---------------------------------------------------------------------------
# Scenario loading
# ---------------------------------------------------------------------------


REQUIRED_SCENARIO_FIELDS = (
    "scenario_id",
    "domain",
    "description",
    "input",
    "expected",
)


def load_scenario(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HarnessError(f"scenario not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HarnessError(f"scenario {path} is not valid JSON: {exc}") from exc
    for required in REQUIRED_SCENARIO_FIELDS:
        if required not in data:
            raise HarnessError(
                f"scenario {path} missing required field {required!r}",
            )
    return data


def load_scenarios(domain: str) -> list[dict[str, Any]]:
    if domain not in SUPPORTED_DOMAINS:
        raise HarnessError(
            f"domain {domain!r} not supported by the pilot; "
            f"expected one of {SUPPORTED_DOMAINS}",
        )
    scenario_dir = SCENARIOS_ROOT / domain
    if not scenario_dir.exists():
        return []
    scenarios = []
    for path in sorted(scenario_dir.glob("*.json")):
        if path.parent.name == "transcripts":
            continue
        scenarios.append(load_scenario(path))
    return scenarios


# ---------------------------------------------------------------------------
# Snapshot composition — mirrors what the live skill receives
# ---------------------------------------------------------------------------


def _recovery_snapshot_block(scenario_input: dict[str, Any]) -> dict[str, Any]:
    """Build the ``snapshot.recovery`` dict the skill consumes.

    Scenarios author evidence + raw_summary + vendor signals; the harness
    runs the real ``classify`` + ``policy`` modules to fill the rest.
    This is exactly the shape ``hai state snapshot --evidence-json …``
    emits for the recovery block.
    """

    from health_agent_infra.core.config import load_thresholds
    from health_agent_infra.domains.recovery.classify import (
        classify_recovery_state,
    )
    from health_agent_infra.domains.recovery.policy import (
        evaluate_recovery_policy,
    )

    evidence = dict(scenario_input.get("evidence") or {})
    raw_summary = dict(scenario_input.get("raw_summary") or {})
    today = dict(scenario_input.get("today") or {})
    thresholds = load_thresholds()

    classified = classify_recovery_state(evidence, raw_summary, thresholds=thresholds)
    policy = evaluate_recovery_policy(classified, raw_summary, thresholds=thresholds)

    return {
        "evidence": evidence,
        "raw_summary": raw_summary,
        "classified_state": _dataclass_to_dict(classified),
        "policy_result": _dataclass_to_dict(policy),
        "today": today,
        "missingness": scenario_input.get("missingness") or {},
    }


def _dataclass_to_dict(obj: Any) -> Any:
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_dataclass_to_dict(v) for v in obj]
    return obj


def compose_snapshot(scenario: dict[str, Any]) -> dict[str, Any]:
    """Compose the full snapshot block the skill would read."""

    domain = scenario["domain"]
    if domain != "recovery":
        raise HarnessError(
            f"pilot only handles domain=recovery; got {domain!r}",
        )
    block = _recovery_snapshot_block(scenario["input"])
    return {
        "as_of_date": scenario["input"].get("for_date"),
        "user_id": scenario["input"].get("user_id", "u_eval"),
        "recovery": block,
    }


# ---------------------------------------------------------------------------
# Backends — live / replay / demo
# ---------------------------------------------------------------------------


@dataclass
class Transcript:
    scenario_id: str
    source: str               # "claude_code_subprocess" | "hand_authored_reference" | ...
    recorded_at: str
    recommendation: dict[str, Any]
    notes: Optional[str] = None
    path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "source": self.source,
            "recorded_at": self.recorded_at,
            "notes": self.notes,
            "recommendation": self.recommendation,
        }


def transcripts_dir(scenario_id: str, domain: str = "recovery") -> Path:
    return SCENARIOS_ROOT / domain / "transcripts" / scenario_id


def load_latest_transcript(scenario_id: str, domain: str = "recovery") -> Optional[Transcript]:
    directory = transcripts_dir(scenario_id, domain=domain)
    if not directory.exists():
        return None
    files = sorted(directory.glob("*.json"))
    if not files:
        return None
    latest = files[-1]
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HarnessError(
            f"transcript {latest} is not valid JSON: {exc}",
        ) from exc
    return Transcript(
        scenario_id=data.get("scenario_id", scenario_id),
        source=data.get("source", "unknown"),
        recorded_at=data.get("recorded_at", ""),
        recommendation=data.get("recommendation") or {},
        notes=data.get("notes"),
        path=str(latest),
    )


def invoke_live(scenario: dict[str, Any]) -> Transcript:
    """Invoke Claude Code as a subprocess against SKILL.md.

    Opt-in: requires ``HAI_SKILL_HARNESS_LIVE=1`` and ``claude`` on PATH.
    Writes the transcript to disk under the scenario's transcripts
    directory and returns the parsed ``Transcript``.
    """

    if os.environ.get("HAI_SKILL_HARNESS_LIVE") != "1":
        raise HarnessError(
            "live mode requires HAI_SKILL_HARNESS_LIVE=1 so it can't be "
            "triggered accidentally from CI or a normal pytest run",
        )

    skill_path = (
        Path(__file__).resolve().parents[3]
        / "src/health_agent_infra/skills/recovery-readiness/SKILL.md"
    )
    if not skill_path.exists():
        raise HarnessError(f"recovery-readiness skill not found at {skill_path}")

    snapshot = compose_snapshot(scenario)
    system_prompt = skill_path.read_text(encoding="utf-8")
    user_prompt = (
        "You are running as the recovery-readiness skill. The snapshot "
        "below is the only bundle you may read. Emit one and only one "
        "JSON object matching the TrainingRecommendation schema. No "
        "prose outside the JSON block.\n\n"
        f"SNAPSHOT:\n{json.dumps(snapshot, indent=2)}\n"
    )

    cmd = [
        "claude",
        "--print",
        "--output-format", "json",
        "--append-system-prompt", system_prompt,
        user_prompt,
    ]
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except FileNotFoundError as exc:
        raise HarnessError(
            "`claude` CLI not found on PATH; install Claude Code or use "
            "--mode replay",
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise HarnessError(
            f"claude subprocess failed (exit {exc.returncode}): {exc.stderr!r}",
        ) from exc

    raw = proc.stdout.strip()
    recommendation = _parse_recommendation_from_claude_output(raw)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    transcript = Transcript(
        scenario_id=scenario["scenario_id"],
        source="claude_code_subprocess",
        recorded_at=stamp,
        recommendation=recommendation,
    )
    out_dir = transcripts_dir(scenario["scenario_id"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stamp}.json"
    out_path.write_text(
        json.dumps(transcript.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    transcript.path = str(out_path)
    return transcript


def _parse_recommendation_from_claude_output(raw: str) -> dict[str, Any]:
    """Claude Code's ``--output-format json`` wraps the model response;
    the model response itself should be a JSON object. Be forgiving if
    the response comes back double-wrapped or with text around it."""

    try:
        outer = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"claude stdout was not JSON: {exc!r} raw={raw[:200]!r}")

    candidate: Any = outer
    if isinstance(outer, dict) and "result" in outer and isinstance(outer["result"], str):
        candidate = outer["result"]

    if isinstance(candidate, str):
        candidate = candidate.strip()
        first = candidate.find("{")
        last = candidate.rfind("}")
        if first == -1 or last == -1 or last <= first:
            raise HarnessError("no JSON object found in claude response text")
        try:
            candidate = json.loads(candidate[first : last + 1])
        except json.JSONDecodeError as exc:
            raise HarnessError(f"failed to parse JSON object from claude response: {exc}")

    if not isinstance(candidate, dict):
        raise HarnessError(
            f"expected a recommendation dict, got {type(candidate).__name__}",
        )
    return candidate


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


CORRECTNESS_AXES = (
    "schema_valid",
    "action_matches",
    "confidence_within_bound",
    "policy_decisions_preserved",
    "action_detail_required_keys",
    "recommendation_id_format",
)

RUBRIC_AXES = (
    "band_references",
    "uncertainty_tokens",
    "forbidden_tokens",
)

_CONFIDENCE_RANK = {"low": 0, "moderate": 1, "high": 2}


@dataclass
class AxisResult:
    verdict: str  # "pass" | "fail" | "skipped"
    detail: Any = None


@dataclass
class ScenarioScore:
    scenario_id: str
    transcript_source: str
    correctness: dict[str, AxisResult] = field(default_factory=dict)
    rubric: dict[str, dict[str, Any]] = field(default_factory=dict)
    rubric_mean: Optional[float] = None
    correctness_passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "transcript_source": self.transcript_source,
            "correctness_passed": self.correctness_passed,
            "correctness": {
                axis: {"verdict": r.verdict, "detail": r.detail}
                for axis, r in self.correctness.items()
            },
            "rubric": dict(self.rubric),
            "rubric_mean": self.rubric_mean,
        }


def _score_correctness(
    recommendation: dict[str, Any],
    scenario: dict[str, Any],
) -> dict[str, AxisResult]:
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    expected = scenario.get("expected") or {}
    results: dict[str, AxisResult] = {}

    try:
        validate_recommendation_dict(recommendation)
        results["schema_valid"] = AxisResult("pass")
    except RecommendationValidationError as exc:
        results["schema_valid"] = AxisResult(
            "fail", {"invariant": exc.invariant, "message": str(exc)},
        )

    expected_action = expected.get("action")
    if expected_action is None:
        results["action_matches"] = AxisResult("skipped", "no expectation")
    else:
        actual = recommendation.get("action")
        if actual == expected_action:
            results["action_matches"] = AxisResult("pass", actual)
        else:
            results["action_matches"] = AxisResult(
                "fail", {"expected": expected_action, "actual": actual},
            )

    bound = expected.get("confidence_at_or_below")
    if bound is None:
        results["confidence_within_bound"] = AxisResult("skipped", "no bound")
    else:
        actual_conf = recommendation.get("confidence")
        bound_rank = _CONFIDENCE_RANK.get(bound)
        actual_rank = _CONFIDENCE_RANK.get(actual_conf or "")
        if bound_rank is None or actual_rank is None:
            results["confidence_within_bound"] = AxisResult(
                "fail", {"expected_bound": bound, "actual": actual_conf},
            )
        elif actual_rank <= bound_rank:
            results["confidence_within_bound"] = AxisResult(
                "pass", {"bound": bound, "actual": actual_conf},
            )
        else:
            results["confidence_within_bound"] = AxisResult(
                "fail", {"bound": bound, "actual": actual_conf},
            )

    if expected.get("policy_decisions_preserved") is True:
        expected_pd = _expected_policy_decisions(scenario)
        actual_pd = _normalise_policy_decisions(
            recommendation.get("policy_decisions") or [],
        )
        expected_norm = _normalise_policy_decisions(expected_pd)
        if actual_pd == expected_norm:
            results["policy_decisions_preserved"] = AxisResult("pass")
        else:
            results["policy_decisions_preserved"] = AxisResult(
                "fail",
                {"expected": expected_norm, "actual": actual_pd},
            )
    else:
        results["policy_decisions_preserved"] = AxisResult(
            "skipped", "not required",
        )

    required_detail_keys = expected.get("action_detail_required_keys")
    if required_detail_keys is None:
        results["action_detail_required_keys"] = AxisResult(
            "skipped", "no expectation",
        )
    else:
        detail = recommendation.get("action_detail") or {}
        if not isinstance(detail, dict):
            results["action_detail_required_keys"] = AxisResult(
                "fail", {"expected_keys": required_detail_keys, "actual": detail},
            )
        else:
            missing = [k for k in required_detail_keys if k not in detail]
            if missing:
                results["action_detail_required_keys"] = AxisResult(
                    "fail",
                    {"missing_keys": missing, "actual_detail": detail},
                )
            else:
                results["action_detail_required_keys"] = AxisResult(
                    "pass", list(required_detail_keys),
                )

    expected_id_pattern = expected.get("recommendation_id_pattern")
    if expected_id_pattern is None:
        results["recommendation_id_format"] = AxisResult(
            "skipped", "no expectation",
        )
    else:
        import re

        actual_id = recommendation.get("recommendation_id") or ""
        if re.fullmatch(expected_id_pattern, actual_id):
            results["recommendation_id_format"] = AxisResult("pass", actual_id)
        else:
            results["recommendation_id_format"] = AxisResult(
                "fail",
                {"pattern": expected_id_pattern, "actual": actual_id},
            )
    return results


def _expected_policy_decisions(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    """Recompute the policy decisions the runtime produced for this
    scenario — these are what the skill must echo verbatim."""

    from health_agent_infra.core.config import load_thresholds
    from health_agent_infra.domains.recovery.classify import (
        classify_recovery_state,
    )
    from health_agent_infra.domains.recovery.policy import (
        evaluate_recovery_policy,
    )

    scenario_input = scenario["input"]
    evidence = dict(scenario_input.get("evidence") or {})
    raw_summary = dict(scenario_input.get("raw_summary") or {})
    thresholds = load_thresholds()
    classified = classify_recovery_state(evidence, raw_summary, thresholds=thresholds)
    policy = evaluate_recovery_policy(classified, raw_summary, thresholds=thresholds)
    return [
        {"rule_id": d.rule_id, "decision": d.decision, "note": d.note}
        for d in policy.policy_decisions
    ]


def _normalise_policy_decisions(
    decisions: Iterable[dict[str, Any]],
) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for d in decisions:
        if not isinstance(d, dict):
            continue
        out.append((
            str(d.get("rule_id", "")),
            str(d.get("decision", "")),
            str(d.get("note", "")),
        ))
    return sorted(out)


def _score_rubric(
    recommendation: dict[str, Any],
    scenario: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], float]:
    """Token-presence rubric. Each sub-axis returns a 0/1/2 score:

    - 2 — every required token present, nothing forbidden.
    - 1 — partial coverage; at least one required token missing, or one
      forbidden token leaked through but the required ones are there.
    - 0 — none of the required tokens present, or a forbidden token
      present with required ones missing.
    """

    expected = scenario.get("expected") or {}
    rationale_text = " ".join(
        str(r).lower() for r in (recommendation.get("rationale") or [])
    )
    uncertainty = [
        str(t).lower() for t in (recommendation.get("uncertainty") or [])
    ]

    # band_references
    bands_required = [b.lower() for b in expected.get("rationale_must_reference_bands", [])]
    if bands_required:
        hits = [b for b in bands_required if b in rationale_text]
        ratio = len(hits) / len(bands_required)
        if ratio == 1.0:
            band_score = 2
        elif ratio >= 0.5:
            band_score = 1
        else:
            band_score = 0
        band_detail = {"required": bands_required, "hits": hits}
    else:
        band_score = 2
        band_detail = {"required": [], "hits": []}

    # uncertainty tokens — must_contain (positive signal) and
    # must_not_contain (forbidden signal) scored together.
    u_required = [t.lower() for t in expected.get("uncertainty_must_contain", [])]
    u_forbidden = [t.lower() for t in expected.get("uncertainty_must_not_contain", [])]
    missing_required = [t for t in u_required if t not in uncertainty]
    present_forbidden = [t for t in u_forbidden if t in uncertainty]
    if not missing_required and not present_forbidden:
        uncertainty_score = 2
    elif not missing_required and present_forbidden:
        uncertainty_score = 1
    elif missing_required and not present_forbidden:
        uncertainty_score = 1 if len(missing_required) < len(u_required) else 0
    else:
        uncertainty_score = 0
    uncertainty_detail = {
        "required": u_required,
        "forbidden": u_forbidden,
        "actual": uncertainty,
        "missing_required": missing_required,
        "present_forbidden": present_forbidden,
    }

    # forbidden_tokens — banned diagnosis-shaped tokens in rationale. We
    # re-check via the writeback validator's list so the rubric stays in
    # sync with the runtime's enforcement.
    from health_agent_infra.core.validate import BANNED_TOKENS

    leaked = [t for t in BANNED_TOKENS if t in rationale_text]
    forbidden_score = 2 if not leaked else 0
    forbidden_detail = {"leaked_banned_tokens": leaked}

    rubric = {
        "band_references": {"score": band_score, "detail": band_detail},
        "uncertainty_tokens": {"score": uncertainty_score, "detail": uncertainty_detail},
        "forbidden_tokens": {"score": forbidden_score, "detail": forbidden_detail},
    }
    mean = (band_score + uncertainty_score + forbidden_score) / 3.0
    return rubric, round(mean, 2)


def score_transcript(
    scenario: dict[str, Any], transcript: Transcript,
) -> ScenarioScore:
    correctness = _score_correctness(transcript.recommendation, scenario)
    rubric, mean = _score_rubric(transcript.recommendation, scenario)
    correctness_passed = all(
        r.verdict in ("pass", "skipped") for r in correctness.values()
    )
    return ScenarioScore(
        scenario_id=scenario["scenario_id"],
        transcript_source=transcript.source,
        correctness=correctness,
        rubric=rubric,
        rubric_mean=mean,
        correctness_passed=correctness_passed,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _run(
    domain: str,
    mode: str,
    scenario_filter: Optional[str] = None,
) -> list[ScenarioScore]:
    scenarios = load_scenarios(domain)
    if scenario_filter:
        scenarios = [s for s in scenarios if s["scenario_id"] == scenario_filter]
        if not scenarios:
            raise HarnessError(
                f"no scenario matches id {scenario_filter!r} under domain {domain!r}",
            )

    scores: list[ScenarioScore] = []
    for scenario in scenarios:
        transcript = _get_transcript(scenario, mode=mode, domain=domain)
        if transcript is None:
            scores.append(ScenarioScore(
                scenario_id=scenario["scenario_id"],
                transcript_source="missing",
                correctness={
                    "schema_valid": AxisResult(
                        "skipped", "no transcript available for this scenario",
                    ),
                },
                rubric={},
                rubric_mean=None,
                correctness_passed=False,
            ))
            continue
        scores.append(score_transcript(scenario, transcript))
    return scores


def _get_transcript(
    scenario: dict[str, Any], *, mode: str, domain: str,
) -> Optional[Transcript]:
    if mode == "live":
        return invoke_live(scenario)
    if mode == "replay":
        return load_latest_transcript(scenario["scenario_id"], domain=domain)
    if mode == "demo":
        _emit_demo_prompt(scenario)
        return None
    raise HarnessError(f"unknown mode {mode!r}")


def _emit_demo_prompt(scenario: dict[str, Any]) -> None:
    snapshot = compose_snapshot(scenario)
    print("# scenario:", scenario["scenario_id"])
    print("# description:", scenario["description"])
    print("# --- snapshot (paste into your agent after SKILL.md) ---")
    print(json.dumps(snapshot, indent=2))
    print("# --- expectations (used by the scorer after you paste a response back) ---")
    print(json.dumps(scenario.get("expected") or {}, indent=2))
    print()


def _print_report(scores: list[ScenarioScore]) -> None:
    if not scores:
        print("no scenarios scored")
        return

    correctness_pass = sum(1 for s in scores if s.correctness_passed)
    correctness_total = len(scores)
    rubric_means = [s.rubric_mean for s in scores if s.rubric_mean is not None]
    rubric_avg = (sum(rubric_means) / len(rubric_means)) if rubric_means else None

    print("=== Phase E skill-harness pilot — report ===")
    print()
    print(
        "[A] Deterministic correctness: "
        f"{correctness_pass}/{correctness_total} scenarios passed",
    )
    print(
        "[B] Rationale rubric: "
        f"mean score {rubric_avg:.2f}/2.00"
        if rubric_avg is not None
        else "[B] Rationale rubric: no rubric scores available",
    )
    print()
    for s in scores:
        mark = "PASS" if s.correctness_passed else "FAIL"
        src = s.transcript_source
        rubric = f"{s.rubric_mean:.2f}" if s.rubric_mean is not None else "—"
        print(f"  [{mark}] {s.scenario_id}   (transcript={src}, rubric={rubric})")
        if not s.correctness_passed:
            for axis, r in s.correctness.items():
                if r.verdict == "fail":
                    print(f"      - correctness.{axis}: FAIL {r.detail}")
        for axis, body in s.rubric.items():
            if body["score"] < 2:
                print(f"      - rubric.{axis}: {body['score']}/2 {body['detail']}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="skill_harness.runner",
        description=(
            "Phase E skill-harness pilot. Scores skill-emitted "
            "TrainingRecommendations along separated correctness and "
            "rationale-rubric axes. Opt-in; not run by CI."
        ),
    )
    parser.add_argument("--domain", choices=list(SUPPORTED_DOMAINS), default="recovery")
    parser.add_argument(
        "--mode",
        choices=("replay", "live", "demo"),
        default="replay",
        help=(
            "replay: load latest committed transcript per scenario. "
            "live: invoke Claude Code subprocess (opt-in). "
            "demo: print prompt + expectations for hand invocation."
        ),
    )
    parser.add_argument(
        "--scenario-id",
        default=None,
        help="optional: restrict to a single scenario",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the full score payload as JSON",
    )
    args = parser.parse_args(argv)

    try:
        scores = _run(args.domain, args.mode, scenario_filter=args.scenario_id)
    except HarnessError as exc:
        print(f"skill-harness error: {exc}", file=sys.stderr)
        return 2

    if args.mode == "demo":
        return 0

    if args.json:
        payload = {
            "mode": args.mode,
            "domain": args.domain,
            "scores": [s.to_dict() for s in scores],
        }
        print(json.dumps(payload, indent=2))
    else:
        _print_report(scores)

    all_passed_correctness = all(s.correctness_passed for s in scores)
    return 0 if all_passed_correctness else 1


if __name__ == "__main__":
    sys.exit(main())
