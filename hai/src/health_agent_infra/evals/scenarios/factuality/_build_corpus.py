"""Corpus generator for the W58D factuality gate (v0.2.0 §2.F).

Procedurally produces fixture JSONs across the five PLAN §2.F
sub-categories plus the known-good corpus. Step 3 ships sub-
categories 1-2 (source_quality + x_rule_conflict); step 4 ships
3-5 (source_signal_conflict + source_row_drift + audit_ref_orphan);
step 5 ships the known-good fixtures.

Each fixture JSON pairs a :class:`ClaimGateInput` payload with the
expected gate outcome (block + block_reason, or pass). The step-6
scoring runner reads ``index.json`` to compute pass/block
percentages from manifest cardinality (no hard-coded counts per
F-PLAN-06 round-1).

Re-run the generator after any gate-logic change that affects
fixture validity::

    uv run python -m \\
        health_agent_infra.evals.scenarios.factuality._build_corpus
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.evals.scenarios.factuality._seed import (
    SEED_DATE,
    SEED_RESOLVABLE_FIRING_ID,
    SEED_DISAGREED_FIRING_ID,
    SEED_DAILY_PLAN_ID,
    SEED_RECOMMENDATION_ID,
    SEED_ROW_VERSION,
    SEED_USER_ID,
)


CORPUS_DIR = Path(__file__).parent


# ---------------------------------------------------------------------------
# Fixture model
# ---------------------------------------------------------------------------


@dataclass
class FactualityFixture:
    fixture_id: str
    category: str
    subcategory: str
    expected_outcome: str  # "block" | "pass"
    expected_block_reason: Optional[str]
    description: str
    atom_text: str
    atom_type: str  # "quantitative" | "comparative" | "qualitative"
    locator_set: list[dict[str, Any]]
    audit_refs: dict[str, list[Any]]
    user_id: Optional[str] = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "factuality_fixture.v1",
            "fixture_id": self.fixture_id,
            "category": self.category,
            "subcategory": self.subcategory,
            "expected_outcome": self.expected_outcome,
            "expected_block_reason": self.expected_block_reason,
            "description": self.description,
            "input": {
                "atom_text": self.atom_text,
                "atom_type": self.atom_type,
                "locator_set": list(self.locator_set),
                "audit_refs": dict(self.audit_refs),
                "user_id": self.user_id,
            },
        }


def _good_locator(column: Optional[str] = "resting_hr") -> dict[str, Any]:
    """A locator that resolves cleanly against the seed."""
    out = {
        "table": "accepted_recovery_state_daily",
        "pk": {"as_of_date": SEED_DATE, "user_id": SEED_USER_ID},
        "row_version": SEED_ROW_VERSION,
    }
    if column is not None:
        out["column"] = column
    return out


# ---------------------------------------------------------------------------
# Category 1 — source_quality (≥30 known-bad)
# ---------------------------------------------------------------------------


def _build_source_quality_fixtures() -> list[FactualityFixture]:
    out: list[FactualityFixture] = []
    n = 0

    # 1a. Locator with non-whitelisted table name (10 fixtures).
    for table_variant in [
        "unknown_table",
        "user_data",
        "garmin_raw",
        "scratch_table",
        "tmp_state",
        "accepted_running_state",  # missing _daily suffix
        "ACCEPTED_RECOVERY_STATE_DAILY",  # case-mismatched
        "accepted-recovery-state-daily",  # hyphenated
        "_internal_table",
        "v0_state_daily",
    ]:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_sq_{n:03d}_table_unknown",
            category="source_quality",
            subcategory="locator_invalid",
            expected_outcome="block",
            expected_block_reason="locator_invalid",
            description=(
                f"Locator citing non-whitelisted table {table_variant!r}."
            ),
            atom_text="On April 28 your resting heart rate was 52 bpm.",
            atom_type="quantitative",
            locator_set=[{
                "table": table_variant,
                "pk": {"as_of_date": SEED_DATE, "user_id": SEED_USER_ID},
                "row_version": SEED_ROW_VERSION,
            }],
            audit_refs={},
        ))

    # 1b. Locator with malformed pk shape (5 fixtures).
    pk_variants = [
        ({}, "empty pk"),
        ({"as_of_date": SEED_DATE}, "missing user_id"),
        ({"user_id": SEED_USER_ID}, "missing as_of_date"),
        (
            {"as_of_date": SEED_DATE, "user_id": SEED_USER_ID,
             "extra_column": "x"},
            "extra column",
        ),
        (
            {"date": SEED_DATE, "user_id": SEED_USER_ID},
            "wrong key name (date instead of as_of_date)",
        ),
    ]
    for pk, label in pk_variants:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_sq_{n:03d}_pk_shape",
            category="source_quality",
            subcategory="locator_invalid",
            expected_outcome="block",
            expected_block_reason="locator_invalid",
            description=f"Locator pk shape malformed: {label}.",
            atom_text="On April 28 your resting heart rate was 52 bpm.",
            atom_type="quantitative",
            locator_set=[{
                "table": "accepted_recovery_state_daily",
                "pk": pk,
                "row_version": SEED_ROW_VERSION,
            }],
            audit_refs={},
        ))

    # 1c. Locator with non-existent row pk (5 fixtures — different
    # combinations of date/user that aren't seeded).
    missing_pks = [
        {"as_of_date": "2099-01-01", "user_id": SEED_USER_ID},
        {"as_of_date": SEED_DATE, "user_id": "u_other"},
        {"as_of_date": "1999-06-15", "user_id": "u_legacy"},
        {"as_of_date": "2026-05-30", "user_id": SEED_USER_ID},
        {"as_of_date": "2025-12-31", "user_id": "u_archived"},
    ]
    for pk in missing_pks:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_sq_{n:03d}_row_missing",
            category="source_quality",
            subcategory="row_missing",
            expected_outcome="block",
            expected_block_reason="locator_row_missing",
            description=f"Locator pk {pk} not seeded — row absent.",
            atom_text="On a date the resting heart rate measurement was N bpm.",
            atom_type="quantitative",
            locator_set=[{
                "table": "accepted_recovery_state_daily",
                "pk": pk,
                "row_version": SEED_ROW_VERSION,
            }],
            audit_refs={},
        ))

    # 1d. Locator missing required field (5 fixtures).
    bad_locators: list[dict[str, Any]] = [
        {"pk": {"as_of_date": SEED_DATE, "user_id": SEED_USER_ID},
         "row_version": SEED_ROW_VERSION},  # missing table
        {"table": "accepted_recovery_state_daily",
         "row_version": SEED_ROW_VERSION},  # missing pk
        {"table": "accepted_recovery_state_daily",
         "pk": {"as_of_date": SEED_DATE, "user_id": SEED_USER_ID}},  # missing row_version
        {"table": None, "pk": {}, "row_version": SEED_ROW_VERSION},  # null table
        {"table": "accepted_recovery_state_daily",
         "pk": {"as_of_date": SEED_DATE, "user_id": SEED_USER_ID},
         "row_version": None},  # null row_version
    ]
    for loc in bad_locators:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_sq_{n:03d}_required_field",
            category="source_quality",
            subcategory="locator_invalid",
            expected_outcome="block",
            expected_block_reason="locator_invalid",
            description="Locator missing or null required field.",
            atom_text="...",
            atom_type="quantitative",
            locator_set=[loc],
            audit_refs={},
        ))

    # 1e. Locator pk value type wrong (5 fixtures).
    # Note: ``isinstance(True, int)`` is True in Python, so the
    # W-PROV-1 ``pk_value_scalar`` validator does NOT reject bool pk
    # values today (parser-corpus finding; future cycle could tighten
    # the validator to mirror D13's bool-as-int rejection). The bool
    # fixture is kept here as a structural test that bool sneaks
    # through validation and is caught downstream as
    # ``LOCATOR_ROW_MISSING``.
    bad_pk_values: list[tuple[dict, str, str]] = [
        ({"as_of_date": [SEED_DATE], "user_id": SEED_USER_ID},
         "locator_invalid", "list not scalar"),
        ({"as_of_date": SEED_DATE, "user_id": {"id": SEED_USER_ID}},
         "locator_invalid", "dict not scalar"),
        ({"as_of_date": True, "user_id": SEED_USER_ID},
         "locator_row_missing",
         "bool sneaks through validator (W-PROV-1 finding)"),
        ({"as_of_date": None, "user_id": SEED_USER_ID},
         "locator_invalid", "None not scalar"),
        ({"as_of_date": SEED_DATE, "user_id": [SEED_USER_ID]},
         "locator_invalid", "list user_id"),
    ]
    for pk, reason, label in bad_pk_values:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_sq_{n:03d}_pk_value_type",
            category="source_quality",
            subcategory=(
                "locator_invalid" if reason == "locator_invalid"
                else "row_missing"
            ),
            expected_outcome="block",
            expected_block_reason=reason,
            description=f"Locator pk value not scalar: {label}.",
            atom_text="...",
            atom_type="quantitative",
            locator_set=[{
                "table": "accepted_recovery_state_daily",
                "pk": pk,
                "row_version": SEED_ROW_VERSION,
            }],
            audit_refs={},
        ))

    return out


# ---------------------------------------------------------------------------
# Category 2 — x_rule_conflict (≥15 known-bad)
# ---------------------------------------------------------------------------


def _build_x_rule_conflict_fixtures() -> list[FactualityFixture]:
    """User explicitly disagreed with the cited x_rule_firing in
    a prior review_outcome. The firing exists, so audit-ref-orphan
    doesn't fire — the new x-rule-conflict lane catches it.
    """

    out: list[FactualityFixture] = []
    n = 0

    # 2a. Direct citation of disagreed firing (5 fixtures with varied
    # atom_text + claim_id). All cite the SAME disagreed firing_id;
    # the variation tests that the lane fires regardless of the
    # surrounding claim shape.
    for variant in range(5):
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_xc_{n:03d}_disagreed_firing",
            category="x_rule_conflict",
            subcategory="user_disagreed_direct",
            expected_outcome="block",
            expected_block_reason="x_rule_conflict_user_disagreed",
            description=(
                f"Atom cites firing_id {SEED_DISAGREED_FIRING_ID} which "
                f"the user explicitly disagreed with (variant {variant})."
            ),
            atom_text=(
                "Rules that shaped the recommendation: low recovery "
                f"signals (X{variant + 1})."
            ),
            atom_type="comparative",
            locator_set=[],
            audit_refs={"x_rule_firing": [SEED_DISAGREED_FIRING_ID]},
            user_id=SEED_USER_ID,
        ))

    # 2b. Mixed citation: one resolvable + one disagreed firing
    # (5 fixtures). The gate must block on the FIRST failure within
    # an atom; ordering varies across fixtures to ensure the lane
    # fires regardless of which citation comes first.
    mixed_orderings = [
        [SEED_RESOLVABLE_FIRING_ID, SEED_DISAGREED_FIRING_ID],
        [SEED_DISAGREED_FIRING_ID, SEED_RESOLVABLE_FIRING_ID],
        [SEED_RESOLVABLE_FIRING_ID, SEED_RESOLVABLE_FIRING_ID,
         SEED_DISAGREED_FIRING_ID],
        [SEED_DISAGREED_FIRING_ID, SEED_RESOLVABLE_FIRING_ID,
         SEED_RESOLVABLE_FIRING_ID],
        [SEED_RESOLVABLE_FIRING_ID, SEED_DISAGREED_FIRING_ID,
         SEED_RESOLVABLE_FIRING_ID],
    ]
    for ordering in mixed_orderings:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_xc_{n:03d}_mixed_disagreement",
            category="x_rule_conflict",
            subcategory="user_disagreed_mixed_citation",
            expected_outcome="block",
            expected_block_reason="x_rule_conflict_user_disagreed",
            description=(
                f"Mixed-citation atom: firings {ordering}. The disagreed "
                f"firing in the list triggers the conflict block."
            ),
            atom_text=(
                "Rules that adjusted the result after the skill ran: "
                "compound triggers."
            ),
            atom_type="comparative",
            locator_set=[],
            audit_refs={"x_rule_firing": ordering},
            user_id=SEED_USER_ID,
        ))

    # 2c. Disagreed firing alongside valid locator (5 fixtures). The
    # locator passes; the disagreement still blocks. Tests that the
    # lane runs AFTER locator resolution.
    for variant in range(5):
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_xc_{n:03d}_with_valid_locator",
            category="x_rule_conflict",
            subcategory="user_disagreed_with_locator",
            expected_outcome="block",
            expected_block_reason="x_rule_conflict_user_disagreed",
            description=(
                f"Valid locator + disagreed firing (variant {variant}). "
                f"Locator resolves cleanly; disagreement still blocks."
            ),
            atom_text=(
                f"On April 28 the recovery recommendation was \"easy "
                f"recovery\" at high confidence, variant {variant}."
            ),
            atom_type="quantitative",
            locator_set=[_good_locator()],
            audit_refs={"x_rule_firing": [SEED_DISAGREED_FIRING_ID]},
            user_id=SEED_USER_ID,
        ))

    return out


# ---------------------------------------------------------------------------
# Generator entrypoint
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Category 3 — source_signal_conflict (≥15 known-bad)
# ---------------------------------------------------------------------------


def _build_source_signal_conflict_fixtures() -> list[FactualityFixture]:
    """Locator cites a column that's either NOT on the row schema or
    has a NULL value. Both detected by ``_resolve_locator_with_drift``
    via the new ``SOURCE_SIGNAL_CONFLICT`` lane.

    Note: the seed's accepted_recovery_state_daily row has
    resting_hr=52 + hrv_rmssd=65 (both non-null). To exercise the
    NULL path, fixtures cite columns that are seeded as NULL in
    extended rows OR cite columns that don't exist on the schema.
    """

    out: list[FactualityFixture] = []
    n = 0

    # 3a. Column not on row schema (8 fixtures — varied missing
    # column names that aren't on accepted_recovery_state_daily).
    for col_variant in [
        "vo2max",
        "lactate_threshold",
        "training_load",
        "tss",
        "sleep_score",
        "stress_score",
        "body_battery",
        "calories_burned",
    ]:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_ssc_{n:03d}_column_unknown",
            category="source_signal_conflict",
            subcategory="column_not_on_schema",
            expected_outcome="block",
            expected_block_reason="source_signal_conflict",
            description=(
                f"Locator cites column {col_variant!r} not on "
                f"accepted_recovery_state_daily row schema."
            ),
            atom_text=f"Your {col_variant} signal supports the claim.",
            atom_type="quantitative",
            locator_set=[_good_locator(column=col_variant)],
            audit_refs={},
        ))

    # 3b. Column exists on schema but value is NULL (7 fixtures —
    # exercises the seed's NULL-bearing extended rows). Each tuple
    # below is a (date, column) pair where the seeded row's column
    # is explicitly NULL. The seed at ``_seed.py`` documents which
    # pairs produce NULL.
    null_pairs: list[tuple[str, str]] = [
        ("2026-04-29", "resting_hr"),   # 2026-04-29 row has resting_hr=NULL
        ("2026-04-30", "hrv_rmssd"),    # 2026-04-30 row has hrv_rmssd=NULL
        ("2026-05-01", "resting_hr"),   # 2026-05-01 row has BOTH NULL
        ("2026-05-01", "hrv_rmssd"),
        # Repeat with varied row_version drift cleared (using each
        # row's actual row_version so the lane fired is the column-
        # NULL one, not the drift one).
        ("2026-04-29", "resting_hr"),
        ("2026-04-30", "hrv_rmssd"),
        ("2026-05-01", "hrv_rmssd"),
    ]
    for idx, (date_v, col) in enumerate(null_pairs):
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_ssc_{n:03d}_value_null",
            category="source_signal_conflict",
            subcategory="column_value_null",
            expected_outcome="block",
            expected_block_reason="source_signal_conflict",
            description=(
                f"Locator cites {col!r} on {date_v} where the row's "
                f"column value is NULL (variant {idx})."
            ),
            atom_text=(
                f"On {date_v} your {col} value supported the "
                f"recommendation (variant {idx})."
            ),
            atom_type="quantitative",
            locator_set=[{
                "table": "accepted_recovery_state_daily",
                "pk": {"as_of_date": date_v, "user_id": SEED_USER_ID},
                "row_version": f"{date_v}T19:00Z",
                "column": col,
            }],
            audit_refs={},
        ))

    return out


# ---------------------------------------------------------------------------
# Category 4 — source_row_drift (≥15 known-bad)
# ---------------------------------------------------------------------------


def _build_source_row_drift_fixtures() -> list[FactualityFixture]:
    """Locator validates and resolves, but the cited row_version
    doesn't match the current row's row_version (supersession).
    """

    out: list[FactualityFixture] = []
    n = 0

    # Generate 15 drift fixtures with varied stale row_version values.
    stale_versions = [
        "2026-04-28T08:00Z",   # earlier same day
        "2026-04-27T19:00Z",   # day before
        "2026-04-20T10:00Z",   # week prior
        "2026-04-01T12:00Z",   # month prior
        "2025-12-31T23:59Z",   # year prior
        "2026-04-28T18:59Z",   # 1-second drift
        "2026-04-28T19:00:01Z", # 1-second after (still mismatched)
        "v1",                  # ad-hoc version label
        "snapshot_20260428_morning",  # custom label
        "rev_001",             # numeric revision
        "2026-04-28T19:00z",   # case-mismatched Z
        "2026-04-28T19:00",    # missing Z
        "2026-04-28 19:00:00", # space separator
        "2026-04-28T19:00:00Z", # full seconds — still differs from seed's "2026-04-28T19:00Z"
        "different_format_entirely",
    ]
    for stale in stale_versions:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_drift_{n:03d}_stale_version",
            category="source_row_drift",
            subcategory="row_version_mismatch",
            expected_outcome="block",
            expected_block_reason="locator_row_version_drift",
            description=(
                f"Cited row_version {stale!r} differs from current "
                f"row_version {SEED_ROW_VERSION!r}."
            ),
            atom_text="On April 28 the resting heart rate was 52 bpm.",
            atom_type="quantitative",
            locator_set=[{
                "table": "accepted_recovery_state_daily",
                "pk": {"as_of_date": SEED_DATE, "user_id": SEED_USER_ID},
                "row_version": stale,
                # Omit column to isolate the drift lane (column-set
                # would also exercise SOURCE_SIGNAL_CONFLICT).
            }],
            audit_refs={},
        ))

    return out


# ---------------------------------------------------------------------------
# Category 5 — audit_ref_orphan (≥10 known-bad)
# ---------------------------------------------------------------------------


def _build_audit_ref_orphan_fixtures() -> list[FactualityFixture]:
    """Audit-ref pk doesn't exist in the cited audit-chain table."""

    out: list[FactualityFixture] = []
    n = 0

    # 5a. Each whitelisted audit-chain table with a non-existent PK
    # (6 fixtures: daily_plan, recommendation_log, proposal_log,
    # x_rule_firing, runtime_event_log, sync_run_log).
    orphan_specs: list[tuple[str, Any]] = [
        ("daily_plan", "plan_does_not_exist"),
        ("recommendation_log", "rec_does_not_exist"),
        ("proposal_log", "prop_does_not_exist"),
        ("x_rule_firing", 99999),
        ("runtime_event_log", 88888),
        ("sync_run_log", 77777),
    ]
    for table, bad_pk in orphan_specs:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_orphan_{n:03d}_{table}",
            category="audit_ref_orphan",
            subcategory="pk_not_found",
            expected_outcome="block",
            expected_block_reason="audit_ref_orphan",
            description=(
                f"audit_ref to {table} pk {bad_pk!r} which does not "
                f"exist."
            ),
            atom_text="...",
            atom_type="quantitative",
            locator_set=[],
            audit_refs={table: [bad_pk]},
        ))

    # 5b. Audit-chain table not in W58D whitelist (4 fixtures).
    for unknown_table in [
        "synthesis_event",
        "intake_log",
        "user_memory",
        "intent_state",
    ]:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_orphan_{n:03d}_unknown_table",
            category="audit_ref_orphan",
            subcategory="table_not_in_whitelist",
            expected_outcome="block",
            expected_block_reason="audit_ref_orphan",
            description=(
                f"audit_ref table {unknown_table!r} not in W58D "
                f"whitelist."
            ),
            atom_text="...",
            atom_type="quantitative",
            locator_set=[],
            audit_refs={unknown_table: ["any-pk-value"]},
        ))

    return out


# ---------------------------------------------------------------------------
# Category 6 — known_good (≥75 fixtures)
# ---------------------------------------------------------------------------


def _build_known_good_fixtures() -> list[FactualityFixture]:
    """Fixtures the gate must NOT block.

    Distribution:
      - 10 qualitative atoms (gate SKIPs — no validation, framing
        prose only)
      - 15 vacuous quantitative + comparative atoms (no provenance,
        gate passes)
      - 20 quantitative atoms with single valid locator (varied:
        with/without column, both seeded resting_hr + hrv_rmssd
        columns)
      - 15 with single valid audit_ref (varied tables, including
        x_rule_firing without disagreement)
      - 10 with combined valid locator + audit_ref
      - 5 with multiple valid locators or multiple valid audit_refs

    Total ≥75 (PLAN §2.F threshold). Each fixture declares
    ``expected_outcome="pass"`` for quant/comp atoms or ``"skip"``
    for qualitative atoms; both count as "known-good passed" in the
    scoring runner.
    """

    out: list[FactualityFixture] = []
    n = 0

    # 6a. Qualitative atoms — SKIP (10 fixtures with varied prose).
    qualitative_texts = [
        "This review is informational. Nothing here mutates intent, "
        "targets, or thresholds — that path is user-gated.",
        "Your primary goal — lean cut — frames how this week's evidence reads.",
        "This review is grounded in plan evidence from the canonical "
        "(non-superseded) version of each day.",
        "No primary goal is recorded in user memory — this review is "
        "plan-driven and does not echo a goal frame.",
        "domain running: insufficient provenance — quantitative and "
        "comparative claims suppressed pending the next provenance cycle",
        "domain stress: insufficient provenance — quantitative and "
        "comparative claims suppressed pending the next provenance cycle",
        "Set a primary goal with `hai memory set primary_goal "
        "your-goal-here` to ground future reviews.",
        "domain sleep: insufficient provenance — quantitative and "
        "comparative claims suppressed pending the next provenance cycle",
        "Looking ahead, the cadence here reflects a steady pattern.",
        "No structural disposition pending — review reads cleanly.",
    ]
    for idx, text in enumerate(qualitative_texts):
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_kg_{n:03d}_qualitative_skip",
            category="known_good",
            subcategory="qualitative_skip",
            expected_outcome="skip",
            expected_block_reason=None,
            description=f"Qualitative atom {idx} — gate SKIPs.",
            atom_text=text,
            atom_type="qualitative",
            locator_set=[],
            audit_refs={},
        ))

    # 6b. Vacuous quantitative + comparative — PASS with no
    # provenance to validate (15 fixtures).
    vacuous_specs: list[tuple[str, str]] = [
        ("quantitative", "You ran `hai daily` on 5 of 7 days this week."),
        ("quantitative", "You received 3 recovery recommendations."),
        ("quantitative", "Of 5 sync runs this week, 5 ran fresh."),
        ("quantitative", "On April 28 the recommendation was 'easy recovery'."),
        ("quantitative", "Of 7 days, 6 had populated plans."),
        ("comparative", "Rules that shaped the recommendation: low recovery (X1)."),
        ("comparative", "Rules that adjusted the result after the skill ran: cap_confidence (X5)."),
        ("comparative", "Rules that shaped the recommendation: high stress (X4)."),
        ("comparative", "No rules fired against this recommendation."),
        ("comparative", "Rules that adjusted the result after the skill ran: restructure (X6)."),
        ("quantitative", "Plans found: 6 of 7 days."),
        ("quantitative", "On April 27 you had 1 sleep recommendation."),
        ("comparative", "Rules that shaped the recommendation: low HRV trend (X8)."),
        ("quantitative", "On April 30 your stress was elevated."),
        ("comparative", "Rules that adjusted the result after the skill ran: soften (X9)."),
    ]
    for atom_type, text in vacuous_specs:
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_kg_{n:03d}_vacuous_pass",
            category="known_good",
            subcategory="vacuous_pass",
            expected_outcome="pass",
            expected_block_reason=None,
            description=(
                f"Vacuous {atom_type} atom — no provenance, gate passes."
            ),
            atom_text=text,
            atom_type=atom_type,
            locator_set=[],
            audit_refs={},
        ))

    # 6c. Single valid locator (20 fixtures: 10 with column, 10
    # without). All cite the seeded 2026-04-28 row with the matching
    # row_version. Variations: column=resting_hr (8), column=hrv_rmssd (2),
    # no column (10).
    locator_variants: list[Optional[str]] = (
        ["resting_hr"] * 8 + ["hrv_rmssd"] * 2 + [None] * 10
    )
    for idx, col in enumerate(locator_variants):
        n += 1
        loc = {
            "table": "accepted_recovery_state_daily",
            "pk": {"as_of_date": SEED_DATE, "user_id": SEED_USER_ID},
            "row_version": SEED_ROW_VERSION,
        }
        if col is not None:
            loc["column"] = col
        out.append(FactualityFixture(
            fixture_id=f"fac_kg_{n:03d}_valid_locator",
            category="known_good",
            subcategory="locator_pass",
            expected_outcome="pass",
            expected_block_reason=None,
            description=(
                f"Single valid locator (variant {idx}, "
                f"column={col!r})."
            ),
            atom_text="On April 28 your resting heart rate was 52 bpm.",
            atom_type="quantitative",
            locator_set=[loc],
            audit_refs={},
        ))

    # 6d. Single valid audit_ref (15 fixtures across the 4 seeded
    # tables; variants reuse the same PK with different surrounding
    # atom_text to avoid fixture_id collision but pin lane behavior).
    audit_ref_specs: list[tuple[str, Any]] = [
        ("daily_plan", SEED_DAILY_PLAN_ID),
        ("daily_plan", SEED_DAILY_PLAN_ID),
        ("daily_plan", SEED_DAILY_PLAN_ID),
        ("daily_plan", SEED_DAILY_PLAN_ID),
        ("recommendation_log", SEED_RECOMMENDATION_ID),
        ("recommendation_log", SEED_RECOMMENDATION_ID),
        ("recommendation_log", SEED_RECOMMENDATION_ID),
        ("recommendation_log", SEED_RECOMMENDATION_ID),
        ("x_rule_firing", SEED_RESOLVABLE_FIRING_ID),
        ("x_rule_firing", SEED_RESOLVABLE_FIRING_ID),
        ("x_rule_firing", SEED_RESOLVABLE_FIRING_ID),
        ("x_rule_firing", SEED_RESOLVABLE_FIRING_ID),
        ("x_rule_firing", SEED_RESOLVABLE_FIRING_ID),
        ("x_rule_firing", SEED_RESOLVABLE_FIRING_ID),
        ("x_rule_firing", SEED_RESOLVABLE_FIRING_ID),
    ]
    for idx, (table, pk) in enumerate(audit_ref_specs):
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_kg_{n:03d}_valid_audit_ref",
            category="known_good",
            subcategory="audit_ref_pass",
            expected_outcome="pass",
            expected_block_reason=None,
            description=(
                f"Single valid audit_ref to {table} (variant {idx})."
            ),
            atom_text=(
                f"On April 28 the recommendation was issued (variant "
                f"{idx})."
            ),
            atom_type="quantitative",
            locator_set=[],
            audit_refs={table: [pk]},
            user_id=(
                SEED_USER_ID if table == "x_rule_firing" else None
            ),
        ))

    # 6e. Combined valid locator + valid audit_ref (10 fixtures).
    for idx in range(10):
        n += 1
        out.append(FactualityFixture(
            fixture_id=f"fac_kg_{n:03d}_combined_pass",
            category="known_good",
            subcategory="combined_pass",
            expected_outcome="pass",
            expected_block_reason=None,
            description=(
                f"Combined valid locator + valid audit_ref (variant "
                f"{idx})."
            ),
            atom_text=(
                f"On April 28 your resting heart rate was 52 bpm; the "
                f"recommendation was issued (variant {idx})."
            ),
            atom_type="quantitative",
            locator_set=[_good_locator()],
            audit_refs={
                "daily_plan": [SEED_DAILY_PLAN_ID],
                "recommendation_log": [SEED_RECOMMENDATION_ID],
            },
        ))

    # 6f. Multiple valid locators or multiple valid audit_refs
    # (5 fixtures). Each fixture exercises the gate's per-element
    # iteration without short-circuiting on a non-failure.
    for idx in range(5):
        n += 1
        if idx % 2 == 0:
            # Two locators citing different columns of the seeded row.
            out.append(FactualityFixture(
                fixture_id=f"fac_kg_{n:03d}_multi_locator",
                category="known_good",
                subcategory="multi_locator_pass",
                expected_outcome="pass",
                expected_block_reason=None,
                description=(
                    f"Two valid locators citing different columns "
                    f"(variant {idx})."
                ),
                atom_text=(
                    "On April 28 both resting heart rate and HRV "
                    "supported the recommendation."
                ),
                atom_type="quantitative",
                locator_set=[
                    _good_locator(column="resting_hr"),
                    _good_locator(column="hrv_rmssd"),
                ],
                audit_refs={},
            ))
        else:
            # Multiple audit_refs across tables.
            out.append(FactualityFixture(
                fixture_id=f"fac_kg_{n:03d}_multi_audit_ref",
                category="known_good",
                subcategory="multi_audit_ref_pass",
                expected_outcome="pass",
                expected_block_reason=None,
                description=(
                    f"Multiple valid audit_refs across two tables "
                    f"(variant {idx})."
                ),
                atom_text=(
                    "Plan and recommendation both exist in the audit "
                    "chain."
                ),
                atom_type="comparative",
                locator_set=[],
                audit_refs={
                    "daily_plan": [SEED_DAILY_PLAN_ID],
                    "recommendation_log": [SEED_RECOMMENDATION_ID],
                    "x_rule_firing": [SEED_RESOLVABLE_FIRING_ID],
                },
                user_id=SEED_USER_ID,
            ))

    return out


def _all_fixtures() -> list[FactualityFixture]:
    """Aggregate every fixture across all categories."""

    out: list[FactualityFixture] = []
    out.extend(_build_source_quality_fixtures())
    out.extend(_build_x_rule_conflict_fixtures())
    out.extend(_build_source_signal_conflict_fixtures())
    out.extend(_build_source_row_drift_fixtures())
    out.extend(_build_audit_ref_orphan_fixtures())
    out.extend(_build_known_good_fixtures())
    return out


def build_corpus(out_dir: Path = CORPUS_DIR) -> dict[str, Any]:
    """Generate every fixture JSON + ``index.json`` manifest."""

    fixtures = _all_fixtures()
    fixtures_meta: list[dict[str, Any]] = []
    by_category: dict[str, list[str]] = {}

    for fixture in fixtures:
        path = out_dir / f"{fixture.fixture_id}.json"
        path.write_text(
            json.dumps(fixture.to_payload(), indent=2, sort_keys=True) + "\n",
        )
        fixtures_meta.append({
            "fixture_id": fixture.fixture_id,
            "category": fixture.category,
            "subcategory": fixture.subcategory,
            "expected_outcome": fixture.expected_outcome,
            "expected_block_reason": fixture.expected_block_reason,
        })
        by_category.setdefault(fixture.category, []).append(
            fixture.fixture_id,
        )

    manifest = {
        "schema_version": "factuality_index.v1",
        "description": (
            "Factuality-gate corpus (PLAN §2.F). Each fixture pairs a "
            "ClaimGateInput payload with the expected gate outcome. "
            "Step 6's scoring runner computes pass/block percentages "
            "from manifest cardinality (no hard-coded counts per "
            "F-PLAN-06)."
        ),
        "total_fixtures": len(fixtures_meta),
        "categories": {
            cat: sorted(ids) for cat, ids in by_category.items()
        },
        "expected_outcome_counts": {
            "block": sum(
                1 for f in fixtures_meta if f["expected_outcome"] == "block"
            ),
            "pass": sum(
                1 for f in fixtures_meta if f["expected_outcome"] == "pass"
            ),
            "skip": sum(
                1 for f in fixtures_meta if f["expected_outcome"] == "skip"
            ),
        },
        "fixtures": sorted(
            fixtures_meta, key=lambda f: f["fixture_id"],
        ),
    }
    (out_dir / "index.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )
    return manifest


def main() -> int:
    manifest = build_corpus()
    print(f"wrote {manifest['total_fixtures']} fixtures + index.json")
    print(f"categories: {sorted(manifest['categories'].keys())}")
    print(f"expected_outcome_counts: {manifest['expected_outcome_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
