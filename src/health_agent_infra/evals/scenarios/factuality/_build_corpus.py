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
    bad_locators = [
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


def _all_fixtures() -> list[FactualityFixture]:
    """Aggregate every fixture across all currently-implemented
    categories. Step 4 will extend this with sub-categories 3-5;
    step 5 with the known-good corpus. The function signature stays
    stable so the scoring runner just calls it.
    """

    out: list[FactualityFixture] = []
    out.extend(_build_source_quality_fixtures())
    out.extend(_build_x_rule_conflict_fixtures())
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
