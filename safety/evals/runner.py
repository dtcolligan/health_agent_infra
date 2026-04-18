"""Scenario loader + scorer for the v1 eval framework.

Two scenario kinds are supported today:

- ``kind="domain"`` — a ``classify`` + ``policy`` pass against a frozen
  ``evidence`` / ``raw_summary`` bundle. Scored on per-band matches and
  policy decision (``forced_action``, ``capped_confidence``, rule-id
  firings).

- ``kind="synthesis"`` — a ``run_synthesis`` pass against a frozen
  ``snapshot`` + ``proposals`` bundle (using an in-memory SQLite DB).
  Scored on X-rule firings (rule ids + tiers + affected domains) and
  final recommendation actions / confidences.

What the runner deliberately does NOT score:

- Skill narration quality (rationale prose, uncertainty prose). Requires
  invoking the daily-plan-synthesis / per-domain skills via a live
  Claude Code agent subprocess. Per Phase 2.5 Track B Condition 3 this
  is a deferred follow-up; scenarios mark those axes with
  ``skipped_requires_agent_harness``.

The runner is import-safe: it has no module-level I/O and does not
touch the user's DB or config unless a scenario says to.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# Scenario discovery
# ---------------------------------------------------------------------------

EVALS_ROOT = Path(__file__).resolve().parent
SCENARIOS_ROOT = EVALS_ROOT / "scenarios"
SUPPORTED_DOMAINS = (
    "recovery",
    "running",
    "sleep",
    "stress",
    "strength",
    "nutrition",
)


class EvalRunError(RuntimeError):
    """Raised when a scenario cannot be loaded or executed."""


def _scenario_dir(kind: str, domain: Optional[str]) -> Path:
    if kind == "synthesis":
        return SCENARIOS_ROOT / "synthesis"
    if kind == "domain":
        if domain is None:
            raise EvalRunError("domain scenarios require a --domain value")
        if domain not in SUPPORTED_DOMAINS:
            raise EvalRunError(
                f"unsupported domain {domain!r}; expected one of {SUPPORTED_DOMAINS}",
            )
        return SCENARIOS_ROOT / domain
    raise EvalRunError(f"unknown scenario kind {kind!r}")


def load_scenario(path: Path) -> dict[str, Any]:
    """Load a single scenario JSON file, validating the shared envelope."""

    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise EvalRunError(f"scenario not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvalRunError(f"scenario {path} is not valid JSON: {exc}") from exc

    for required in ("scenario_id", "kind", "description", "expected"):
        if required not in data:
            raise EvalRunError(
                f"scenario {path} missing required field {required!r}",
            )
    return data


def load_scenarios(kind: str, domain: Optional[str] = None) -> list[dict[str, Any]]:
    """Discover + load all scenarios for a kind/domain pair, sorted by id."""

    scenario_dir = _scenario_dir(kind, domain)
    if not scenario_dir.exists():
        return []
    scenarios = [load_scenario(p) for p in sorted(scenario_dir.glob("*.json"))]
    # Each scenario's kind must agree with the requested kind.
    for s in scenarios:
        if s["kind"] != kind:
            raise EvalRunError(
                f"scenario {s.get('scenario_id')} kind={s['kind']!r} "
                f"does not match requested kind {kind!r}",
            )
    return scenarios


# ---------------------------------------------------------------------------
# Result + score dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ScenarioScore:
    scenario_id: str
    passed: bool
    axes: dict[str, str]   # axis_name → "pass" | "fail" | "skipped_requires_agent_harness"
    diffs: dict[str, Any]  # axis_name → structured diff when failed

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "axes": dict(self.axes),
            "diffs": dict(self.diffs),
        }


@dataclass
class DomainScenarioResult:
    scenario_id: str
    domain: str
    classified: dict[str, Any]
    policy: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "domain": self.domain,
            "classified": dict(self.classified),
            "policy": dict(self.policy),
        }


@dataclass
class SynthesisScenarioResult:
    scenario_id: str
    daily_plan_id: str
    phase_a_firings: list[dict[str, Any]] = field(default_factory=list)
    phase_b_firings: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    # Populated when the scenario authored an expected validation error,
    # e.g. s4-style stale-schema proposals that must be rejected at the
    # writeback layer before synthesis ever runs.
    validation_errors: list[dict[str, Any]] = field(default_factory=list)
    synthesis_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "daily_plan_id": self.daily_plan_id,
            "phase_a_firings": list(self.phase_a_firings),
            "phase_b_firings": list(self.phase_b_firings),
            "recommendations": list(self.recommendations),
            "validation_errors": list(self.validation_errors),
            "synthesis_error": self.synthesis_error,
        }


# ---------------------------------------------------------------------------
# Domain runner
# ---------------------------------------------------------------------------


def _domain_classify(
    domain: str,
    scenario_input: dict[str, Any],
    thresholds: dict[str, Any],
) -> Any:
    """Dispatch to the domain classifier with the input shape it expects.

    Recovery takes ``(evidence, raw_summary)``; every other domain takes
    a single ``signals`` dict. Scenarios author one or the other (or both
    in the recovery case) inside ``input``.
    """

    evidence = dict(scenario_input.get("evidence") or {})
    raw_summary = dict(scenario_input.get("raw_summary") or {})
    signals = dict(scenario_input.get("signals") or {})

    if domain == "recovery":
        from health_agent_infra.domains.recovery.classify import classify_recovery_state
        return classify_recovery_state(evidence, raw_summary, thresholds=thresholds)
    if domain == "running":
        from health_agent_infra.domains.running.classify import classify_running_state
        return classify_running_state(signals, thresholds=thresholds)
    if domain == "sleep":
        from health_agent_infra.domains.sleep.classify import classify_sleep_state
        return classify_sleep_state(signals, thresholds=thresholds)
    if domain == "stress":
        from health_agent_infra.domains.stress.classify import classify_stress_state
        return classify_stress_state(signals, thresholds=thresholds)
    if domain == "strength":
        from health_agent_infra.domains.strength.classify import classify_strength_state
        return classify_strength_state(signals, thresholds=thresholds)
    if domain == "nutrition":
        from health_agent_infra.domains.nutrition.classify import classify_nutrition_state
        return classify_nutrition_state(signals, thresholds=thresholds)
    raise EvalRunError(f"no classifier wired for domain {domain!r}")


def _domain_policy(
    domain: str,
    classified: Any,
    scenario_input: dict[str, Any],
    thresholds: dict[str, Any],
) -> Any:
    """Dispatch to the domain policy with the input shape it expects.

    Recovery policy consumes ``raw_summary``; every other domain's policy
    consumes the same ``signals`` dict the classifier saw.
    """

    raw_summary = dict(scenario_input.get("raw_summary") or {})
    signals = dict(scenario_input.get("signals") or {})

    if domain == "recovery":
        from health_agent_infra.domains.recovery.policy import evaluate_recovery_policy
        return evaluate_recovery_policy(classified, raw_summary, thresholds=thresholds)
    if domain == "running":
        from health_agent_infra.domains.running.policy import evaluate_running_policy
        return evaluate_running_policy(classified, signals, thresholds=thresholds)
    if domain == "sleep":
        from health_agent_infra.domains.sleep.policy import evaluate_sleep_policy
        return evaluate_sleep_policy(classified, signals, thresholds=thresholds)
    if domain == "stress":
        from health_agent_infra.domains.stress.policy import evaluate_stress_policy
        return evaluate_stress_policy(classified, signals, thresholds=thresholds)
    if domain == "strength":
        from health_agent_infra.domains.strength.policy import evaluate_strength_policy
        # Strength policy signature is (classified, thresholds); the
        # classified state already carries volume_ratio + unmatched tokens
        # so there's no signals passthrough.
        return evaluate_strength_policy(classified, thresholds=thresholds)
    if domain == "nutrition":
        from health_agent_infra.domains.nutrition.policy import evaluate_nutrition_policy
        # Nutrition policy signature is (classified, thresholds) — no
        # signals passthrough (classified already captures calorie_deficit
        # and protein_ratio).
        return evaluate_nutrition_policy(classified, thresholds=thresholds)
    raise EvalRunError(f"no policy wired for domain {domain!r}")


def _to_dict(obj: Any) -> Any:
    """Recursive dataclass/tuple → dict/list normaliser.

    Dataclasses (frozen or otherwise) lack a uniform JSON surface; some
    domain modules expose a ``to_dict`` method, others don't. This
    helper prefers ``to_dict`` when present, then falls back to
    ``dataclasses.asdict`` for dataclass instances, then descends into
    tuples/lists/dicts recursively.
    """

    import dataclasses

    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_dict(v) for v in obj]
    return obj


def run_domain_scenario(scenario: dict[str, Any]) -> DomainScenarioResult:
    """Run classify + policy for a domain scenario against a frozen bundle."""

    from health_agent_infra.core.config import load_thresholds

    domain = scenario.get("domain")
    if domain not in SUPPORTED_DOMAINS:
        raise EvalRunError(
            f"domain scenario {scenario.get('scenario_id')!r} "
            f"has invalid domain {domain!r}",
        )
    input_block = dict(scenario.get("input") or {})
    thresholds = load_thresholds()

    classified = _domain_classify(domain, input_block, thresholds)
    policy = _domain_policy(domain, classified, input_block, thresholds)

    return DomainScenarioResult(
        scenario_id=scenario["scenario_id"],
        domain=domain,
        classified=_to_dict(classified),
        policy=_to_dict(policy),
    )


def score_domain_result(
    result: DomainScenarioResult,
    expected: dict[str, Any],
) -> ScenarioScore:
    """Compare a domain-scenario result against the expected envelope."""

    axes: dict[str, str] = {}
    diffs: dict[str, Any] = {}

    # Axis 1 — classified bands. The scenario lists specific keys it cares
    # about (e.g. only sleep_debt_band + coverage_band). Missing-key means
    # the scenario does not assert on it.
    expected_classified = expected.get("classified") or {}
    classified_diff = {}
    for key, exp_value in expected_classified.items():
        actual = result.classified.get(key)
        if actual != exp_value:
            classified_diff[key] = {"expected": exp_value, "actual": actual}
    if classified_diff:
        axes["classified_bands"] = "fail"
        diffs["classified_bands"] = classified_diff
    else:
        axes["classified_bands"] = "pass"

    # Axis 2 — policy firings. The scenario may assert on any subset of:
    #   forced_action, capped_confidence, fired_rule_ids (order-insensitive)
    expected_policy = expected.get("policy") or {}
    policy_diff = {}
    if "forced_action" in expected_policy:
        actual = result.policy.get("forced_action")
        if actual != expected_policy["forced_action"]:
            policy_diff["forced_action"] = {
                "expected": expected_policy["forced_action"],
                "actual": actual,
            }
    if "capped_confidence" in expected_policy:
        actual = result.policy.get("capped_confidence")
        if actual != expected_policy["capped_confidence"]:
            policy_diff["capped_confidence"] = {
                "expected": expected_policy["capped_confidence"],
                "actual": actual,
            }
    if "fired_rule_ids" in expected_policy:
        # Different domain policy dataclasses surface their firings
        # under different keys. Accept the common ones and collapse to
        # one list.
        firings: list[dict[str, Any]] = []
        for key in ("policy_decisions", "rule_firings", "decisions"):
            candidate = result.policy.get(key)
            if isinstance(candidate, (list, tuple)):
                firings.extend(c for c in candidate if isinstance(c, dict))
        # Only include decisions whose tier is not "allow" — evals care
        # about what fired actively. Scenarios can always assert the
        # empty set if they expect nothing to fire.
        active_ids = sorted(
            {f.get("rule_id") for f in firings
             if f.get("decision") not in (None, "allow")}
        )
        expected_ids = sorted(set(expected_policy["fired_rule_ids"]))
        if active_ids != expected_ids:
            policy_diff["fired_rule_ids"] = {
                "expected": expected_ids,
                "actual": active_ids,
            }
    if policy_diff:
        axes["policy_decisions"] = "fail"
        diffs["policy_decisions"] = policy_diff
    else:
        axes["policy_decisions"] = "pass"

    # Axis 3 — skill narration is never invoked here.
    axes["rationale_quality"] = "skipped_requires_agent_harness"

    passed = all(v == "pass" or v.startswith("skipped_") for v in axes.values())
    return ScenarioScore(
        scenario_id=result.scenario_id,
        passed=passed,
        axes=axes,
        diffs=diffs,
    )


# ---------------------------------------------------------------------------
# Synthesis runner
# ---------------------------------------------------------------------------


def _project_scenario_proposal(conn: sqlite3.Connection, raw: dict[str, Any]) -> None:
    """Best-effort projection of a scenario-authored proposal into
    ``proposal_log`` for synthesis to consume.

    Scenarios author proposals in the plan's full shape. The runtime
    expects domain-specific ``schema_version`` strings and a
    ``policy_decisions`` list. Fill sensible defaults so valid scenarios
    don't trip on writeback hygiene at the synthesis layer. If a
    scenario deliberately carries a ``_defect`` marker, it will be
    handed to the writeback validator upstream (never to this helper).
    """

    from health_agent_infra.core.state import project_proposal
    from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS

    payload = dict(raw)
    domain = payload["domain"]
    if domain in PROPOSAL_SCHEMA_VERSIONS and payload.get("schema_version") in (None, "1.0"):
        payload["schema_version"] = PROPOSAL_SCHEMA_VERSIONS[domain]
    payload.setdefault("action_detail", None)
    payload.setdefault("rationale", [])
    payload.setdefault("uncertainty", [])
    payload.setdefault(
        "policy_decisions",
        [{"rule_id": "r1_coverage", "decision": "allow", "note": "eval_fixture"}],
    )
    payload.setdefault("bounded", True)
    project_proposal(conn, payload)


def run_synthesis_scenario(scenario: dict[str, Any]) -> SynthesisScenarioResult:
    """Run ``run_synthesis`` against a frozen scenario bundle in memory.

    Opens a fresh in-memory SQLite database, applies all migrations,
    projects the scenario's proposals, then invokes synthesis. Captures
    final recommendations + firings + any authored validation errors.
    """

    from health_agent_infra.core.state import initialize_database
    from health_agent_infra.core.synthesis import SynthesisError, run_synthesis
    from health_agent_infra.core.writeback.proposal import (
        ProposalValidationError,
        validate_proposal_dict,
    )

    as_of = scenario.get("as_of_date")
    user_id = scenario.get("user_id", "u_eval")
    snapshot = scenario.get("snapshot") or {}
    proposals_in = scenario.get("proposals") or []
    if as_of is None:
        raise EvalRunError(
            f"synthesis scenario {scenario.get('scenario_id')!r} missing as_of_date",
        )

    # Always use an in-memory shared DB so multiple opens reach the same
    # state. initialize_database expects a filesystem path, so we use a
    # tempfile; ScenarioResult never touches disk outside the tmp path.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "eval.db"
        initialize_database(db_path)

        validation_errors: list[dict[str, Any]] = []
        validated_payloads: list[dict[str, Any]] = []
        for p in proposals_in:
            defect = p.get("_defect")
            payload = {k: v for k, v in p.items() if k != "_defect"}
            if defect is not None:
                # Scenario expects writeback validation to catch this. Run
                # validate_proposal_dict; record the rejection verdict.
                try:
                    validate_proposal_dict(payload)
                    validation_errors.append({
                        "proposal_id": payload.get("proposal_id"),
                        "intended_defect": defect,
                        "accepted": True,
                        "error_invariant": None,
                        "error_message": None,
                    })
                except ProposalValidationError as exc:
                    validation_errors.append({
                        "proposal_id": payload.get("proposal_id"),
                        "intended_defect": defect,
                        "accepted": False,
                        "error_invariant": exc.invariant,
                        "error_message": str(exc),
                    })
                continue
            validated_payloads.append(payload)

        from health_agent_infra.core.state import open_connection

        conn = open_connection(db_path)
        try:
            for payload in validated_payloads:
                _project_scenario_proposal(conn, payload)
        finally:
            conn.close()

        synthesis_error: Optional[str] = None
        recommendations: list[dict[str, Any]] = []
        phase_a_firings: list[dict[str, Any]] = []
        phase_b_firings: list[dict[str, Any]] = []
        daily_plan_id = ""

        conn = open_connection(db_path)
        try:
            try:
                result = run_synthesis(
                    conn,
                    for_date=date.fromisoformat(as_of),
                    user_id=user_id,
                    snapshot=snapshot,
                )
                daily_plan_id = result.daily_plan_id
                phase_a_firings = [f.to_dict() for f in result.phase_a_firings]
                phase_b_firings = [f.to_dict() for f in result.phase_b_firings]
            except SynthesisError as exc:
                synthesis_error = str(exc)
        finally:
            conn.close()

        if daily_plan_id:
            conn = open_connection(db_path)
            try:
                cursor = conn.execute(
                    "SELECT recommendation_id, domain, action, payload_json "
                    "FROM recommendation_log WHERE recommendation_id IN "
                    "(" + ",".join("?" * len(result.recommendation_ids)) + ")",
                    tuple(result.recommendation_ids),
                )
                for row in cursor.fetchall():
                    payload = json.loads(row["payload_json"])
                    recommendations.append({
                        "recommendation_id": row["recommendation_id"],
                        "domain": row["domain"],
                        "action": row["action"],
                        "confidence": payload.get("confidence"),
                        "action_detail": payload.get("action_detail"),
                    })
            finally:
                conn.close()

    return SynthesisScenarioResult(
        scenario_id=scenario["scenario_id"],
        daily_plan_id=daily_plan_id,
        phase_a_firings=phase_a_firings,
        phase_b_firings=phase_b_firings,
        recommendations=recommendations,
        validation_errors=validation_errors,
        synthesis_error=synthesis_error,
    )


def score_synthesis_result(
    result: SynthesisScenarioResult,
    expected: dict[str, Any],
) -> ScenarioScore:
    """Compare a synthesis-scenario result against the expected envelope."""

    axes: dict[str, str] = {}
    diffs: dict[str, Any] = {}

    # Axis 1 — X-rule firings (set of rule_ids, order-insensitive).
    expected_rules = expected.get("x_rules_fired")
    if expected_rules is not None:
        actual_rules = sorted({f["rule_id"] for f in result.phase_a_firings}
                              | {f["rule_id"] for f in result.phase_b_firings})
        expected_rules_sorted = sorted(set(expected_rules))
        if actual_rules != expected_rules_sorted:
            axes["x_rules_fired"] = "fail"
            diffs["x_rules_fired"] = {
                "expected": expected_rules_sorted,
                "actual": actual_rules,
            }
        else:
            axes["x_rules_fired"] = "pass"

    # Axis 2 — final actions per domain.
    expected_actions = expected.get("final_actions")
    if expected_actions is not None:
        actual_actions = {r["domain"]: r["action"] for r in result.recommendations}
        action_diff: dict[str, Any] = {}
        for domain, exp_action in expected_actions.items():
            actual = actual_actions.get(domain)
            if actual != exp_action:
                action_diff[domain] = {"expected": exp_action, "actual": actual}
        if action_diff:
            axes["final_actions"] = "fail"
            diffs["final_actions"] = action_diff
        else:
            axes["final_actions"] = "pass"

    # Axis 3 — final confidences per domain.
    expected_conf = expected.get("final_confidences")
    if expected_conf is not None:
        actual_conf = {r["domain"]: r["confidence"] for r in result.recommendations}
        conf_diff: dict[str, Any] = {}
        for domain, exp_c in expected_conf.items():
            actual = actual_conf.get(domain)
            if actual != exp_c:
                conf_diff[domain] = {"expected": exp_c, "actual": actual}
        if conf_diff:
            axes["final_confidences"] = "fail"
            diffs["final_confidences"] = conf_diff
        else:
            axes["final_confidences"] = "pass"

    # Axis 4 — validation errors for scenarios that carry defects.
    expected_validation = expected.get("validation_errors")
    if expected_validation is not None:
        validation_diff: dict[str, Any] = {}
        expected_by_id = {v["proposal_id"]: v for v in expected_validation}
        actual_by_id = {v["proposal_id"]: v for v in result.validation_errors}
        for pid, exp in expected_by_id.items():
            actual = actual_by_id.get(pid)
            if actual is None:
                validation_diff[pid] = {"expected": exp, "actual": None}
                continue
            for k, v in exp.items():
                if actual.get(k) != v:
                    validation_diff.setdefault(pid, {})[k] = {
                        "expected": v, "actual": actual.get(k),
                    }
        if validation_diff:
            axes["validation_errors"] = "fail"
            diffs["validation_errors"] = validation_diff
        else:
            axes["validation_errors"] = "pass"

    # Axis 5 — synthesis error (e.g. s4-style: expect SynthesisError
    # because no proposals landed).
    expected_err = expected.get("synthesis_error")
    if expected_err is not None:
        if expected_err == "expected":
            if result.synthesis_error is None:
                axes["synthesis_error"] = "fail"
                diffs["synthesis_error"] = {
                    "expected": "raised", "actual": "no_error",
                }
            else:
                axes["synthesis_error"] = "pass"
        elif expected_err == "none":
            if result.synthesis_error is not None:
                axes["synthesis_error"] = "fail"
                diffs["synthesis_error"] = {
                    "expected": "no_error", "actual": result.synthesis_error,
                }
            else:
                axes["synthesis_error"] = "pass"

    # Axis 6 — skill narration is never invoked here.
    axes["rationale_quality"] = "skipped_requires_agent_harness"

    passed = all(v == "pass" or v.startswith("skipped_") for v in axes.values())
    return ScenarioScore(
        scenario_id=result.scenario_id,
        passed=passed,
        axes=axes,
        diffs=diffs,
    )


# ---------------------------------------------------------------------------
# Combined runner used by CLI + tests
# ---------------------------------------------------------------------------


def run_scenarios(
    scenarios: Iterable[dict[str, Any]],
) -> list[ScenarioScore]:
    """Execute + score a batch of scenarios. Scenario kind dispatches the runner."""

    scores: list[ScenarioScore] = []
    for scenario in scenarios:
        kind = scenario.get("kind")
        if kind == "domain":
            result = run_domain_scenario(scenario)
            score = score_domain_result(result, scenario.get("expected") or {})
        elif kind == "synthesis":
            result = run_synthesis_scenario(scenario)
            score = score_synthesis_result(result, scenario.get("expected") or {})
        else:
            raise EvalRunError(
                f"scenario {scenario.get('scenario_id')} has unknown kind {kind!r}",
            )
        scores.append(score)
    return scores
