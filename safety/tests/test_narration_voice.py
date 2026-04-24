"""D3 test #7 — voice linter for user-facing narration.

The voice module in ``core/narration/voice.py`` is the shared gate
between the ``reporting`` skill and ``hai today``. It asserts
*absence* of two anti-patterns:

1. Medical / diagnostic language (shares the banned-token set with
   ``core.validate.BANNED_TOKENS`` so payload-layer and prose-layer
   checks never drift).
2. Rule ID leaks (``R1``, ``R3a``, ``X9``, ``require_min_coverage``)
   — those belong in ``hai explain --operator``, not in prose.

These tests are the contract check on that gate:

- Clean snippets (hand-written to mirror real 2026-04-23 output)
  return an empty finding list.
- Each banned token + each rule-id shape produces the expected
  finding category.
- An actually-rendered ``hai today`` bundle lints clean.
"""

from __future__ import annotations

import io
import json
import sqlite3
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.narration import lint_narration
from health_agent_infra.core.narration.voice import LintFinding
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import initialize_database


# ---------------------------------------------------------------------------
# Clean-snippet corpus — 20 real-shape examples
# ---------------------------------------------------------------------------


_CLEAN_SNIPPETS: tuple[str, ...] = (
    "Today, 2026-04-23 — your plan (4 prescriptions, 2 defers).",
    "Green across the board for a quality session.",
    "Mostly defers today — thin evidence from your last pull.",
    "Proceed with your planned session. HRV and sleep both look normal.",
    "Downgrade today's hard session to Zone 2 — resting HR 12% above baseline three days running.",
    "Rest today. You've been training hard and the signals are asking for a break.",
    "Swap today's session for mobility work only — soreness is high.",
    "Keep your usual sleep schedule tonight.",
    "Wind down earlier tonight — sleep debt is accumulating.",
    "Target an earlier bedtime tonight.",
    "Hold today's macro targets.",
    "Bump protein today — yesterday's intake was low relative to training load.",
    "Drink more today — hydration lagged yesterday.",
    "Keep your usual routine. Stress signals are steady.",
    "Add a low-intensity recovery block today.",
    "Not enough information to recommend a training call today. How did yesterday's session land?",
    "Not enough macros logged for today. How did yesterday's eating go?",
    "Proceed with your planned run. Easy pace, conversational effort.",
    "Soften today's intervals to a tempo effort — acute:chronic ratio is elevated.",
    "Cross-train today instead — running legs feel tired, but you still have aerobic capacity.",
)


@pytest.mark.parametrize("snippet", _CLEAN_SNIPPETS)
def test_clean_snippet_has_no_findings(snippet: str):
    assert lint_narration(snippet) == []


# ---------------------------------------------------------------------------
# Medical-language detection
# ---------------------------------------------------------------------------


_MEDICAL_PHRASES: tuple[tuple[str, str], ...] = (
    ("You may have a mild illness today.", "illness"),
    ("This looks like an infection — see a doctor.", "infection"),
    ("Consider whether you have an underlying condition.", "condition"),
    ("Possible overtraining syndrome based on the trend.", "syndrome"),
    ("Your HRV looks like a disease marker.", "disease"),
    ("I cannot diagnose this, but the pattern is concerning.", "diagnose"),
    ("Could be an early diagnosis of adrenal fatigue.", "diagnosis"),
    ("You've been diagnosed with something according to this dashboard.", "diagnosed"),
    ("Feels like a mood disorder pattern.", "disorder"),
    ("You sound sick.", "sick"),
)


@pytest.mark.parametrize("snippet,expected_match", _MEDICAL_PHRASES)
def test_medical_language_triggers_finding(snippet: str, expected_match: str):
    findings = lint_narration(snippet)
    medical_hits = [f for f in findings if f.category == "medical_language"]
    assert any(f.match.lower() == expected_match for f in medical_hits), (
        f"expected medical-language hit for {expected_match!r} in {snippet!r}, "
        f"got {findings}"
    )


def test_medical_language_matching_is_whole_word():
    """``conditional`` should not fire the ``condition`` banned token."""

    findings = lint_narration(
        "That's a conditional recommendation based on whether you run today."
    )
    assert [f for f in findings if f.category == "medical_language"] == []


def test_medical_language_matching_is_case_insensitive():
    findings = lint_narration("POSSIBLE INFECTION in the numbers today.")
    medical = [f for f in findings if f.category == "medical_language"]
    assert len(medical) == 1
    assert medical[0].match.lower() == "infection"


# ---------------------------------------------------------------------------
# Rule-ID leak detection
# ---------------------------------------------------------------------------


_RULE_ID_PHRASES: tuple[tuple[str, str], ...] = (
    ("Rule R1 fired because HRV dropped.", "R1"),
    ("R3a triggered on the last pull.", "R3a"),
    ("X9 suggests bumping protein.", "X9"),
    ("X1a adjusted the intensity downward.", "X1a"),
    ("require_min_coverage blocked the decision.", "require_min_coverage"),
    ("forced_action = defer came from the policy layer.", "forced_action"),
    ("coverage_insufficient means no recommendation today.", "coverage_insufficient"),
)


@pytest.mark.parametrize("snippet,expected_match", _RULE_ID_PHRASES)
def test_rule_id_leak_triggers_finding(snippet: str, expected_match: str):
    findings = lint_narration(snippet)
    rule_hits = [f for f in findings if f.category == "rule_id_leak"]
    assert any(f.match == expected_match for f in rule_hits), (
        f"expected rule-id hit for {expected_match!r} in {snippet!r}, "
        f"got {findings}"
    )


def test_rule_id_pattern_doesnt_false_fire_on_domain_names():
    """``running`` and ``recovery`` must not trigger the rule-id regex."""

    findings = lint_narration(
        "Running and recovery both look normal today."
    )
    assert [f for f in findings if f.category == "rule_id_leak"] == []


def test_lint_finding_carries_span_for_highlighting():
    text = "Rule R1 explains this."
    findings = lint_narration(text)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == "rule_id_leak"
    assert finding.match == "R1"
    assert text[finding.span[0]:finding.span[1]] == "R1"


# ---------------------------------------------------------------------------
# Integration — actual `hai today` output lints clean
# ---------------------------------------------------------------------------


def _seed_today_plan(db: Path, *, user: str, as_of: date) -> None:
    plan_id = canonical_daily_plan_id(as_of, user)
    rec_ids = [
        f"rec_{as_of.isoformat()}_{user}_{domain}_01"
        for domain in (
            "recovery", "sleep", "running", "strength", "stress", "nutrition",
        )
    ]
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO daily_plan (
                daily_plan_id, user_id, for_date, synthesized_at,
                recommendation_ids_json, proposal_ids_json,
                x_rules_fired_json, synthesis_meta_json,
                source, ingest_actor, validated_at, projected_at
            ) VALUES (?, ?, ?, ?, ?, '[]', '[]', NULL,
                      'test', 'test', ?, ?)
            """,
            (
                plan_id, user, as_of.isoformat(),
                "2026-04-23T07:00:00+00:00",
                json.dumps(rec_ids),
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
            ),
        )
        for domain, rec_id in zip(
            ("recovery", "sleep", "running", "strength", "stress", "nutrition"),
            rec_ids,
        ):
            action = {
                "recovery": "proceed_with_planned_session",
                "sleep": "maintain_schedule",
                "running": "proceed_with_planned_run",
                "strength": "proceed_with_planned_session",
                "stress": "maintain_routine",
                "nutrition": "maintain_targets",
            }[domain]
            payload = {
                "recommendation_id": rec_id,
                "domain": domain,
                "action": action,
                "confidence": "moderate",
                "rationale": [f"{domain}_looks_ok"],
                "uncertainty": [],
                "follow_up": {
                    "review_question": f"How did today's {domain} land?",
                },
            }
            conn.execute(
                """
                INSERT INTO recommendation_log (
                    recommendation_id, user_id, for_date, issued_at,
                    action, confidence, bounded, payload_json,
                    source, ingest_actor, produced_at, validated_at,
                    projected_at, domain, daily_plan_id
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'test', 'test',
                          ?, ?, ?, ?, ?)
                """,
                (
                    rec_id, user, as_of.isoformat(),
                    "2026-04-23T07:00:00+00:00",
                    action, "moderate",
                    json.dumps(payload),
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    domain, plan_id,
                ),
            )
        conn.commit()


def test_rendered_hai_today_output_lints_clean(tmp_path: Path):
    """Render a realistic green-day plan through ``hai today`` and lint
    the output. No medical language, no rule-id leaks.
    """

    db = tmp_path / "state.db"
    initialize_database(db)
    user = "u_voice"
    as_of = date(2026, 4, 23)
    _seed_today_plan(db, user=user, as_of=as_of)

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli_main([
            "today",
            "--as-of", as_of.isoformat(),
            "--user-id", user,
            "--db-path", str(db),
            "--format", "plain",
        ])
    assert rc == 0, stderr_buf.getvalue()

    findings = lint_narration(stdout_buf.getvalue())
    assert findings == [], (
        f"hai today output triggered voice-lint findings: {findings}"
    )


def test_lint_finding_is_hashable_for_dedup_use():
    """``LintFinding`` is a frozen dataclass so callers can dedup or
    put findings into sets. A small hash/equality sanity check guards
    against accidentally unfreezing the class later."""

    a = LintFinding(category="medical_language", match="illness", span=(10, 17))
    b = LintFinding(category="medical_language", match="illness", span=(10, 17))
    c = LintFinding(category="rule_id_leak", match="R1", span=(0, 2))
    assert a == b
    assert {a, b, c} == {a, c}
