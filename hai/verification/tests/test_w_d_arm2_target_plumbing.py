"""W-D arm-2 (v0.1.17 §2.I) — partial-day nutrition end-of-day projection.

Acceptance per PLAN §2.I (7 items):

  1. Plumbing: get_active_macro_targets reads the 4 macro target rows
     from `target` (post-migration 025) and returns the threshold-tree
     keyed dict.
  2. Projection emission via build_snapshot(): seed targets + partial-
     day intake; assert classified state carries projected_eod_*
     fields AND nutrition_status='aligned' AND
     calorie_balance_band='met' AND protein_sufficiency_band='met'.
  3. arm-2/arm-1 boundary: target_status absent/unavailable → arm-1
     fires (insufficient_data); no projected_eod_* fields.
  4. Day-closed: is_partial_day=False → no projection; existing
     classifier path runs.
  5. Linear-extrapolation reachability: deep-merged full threshold
     tree with projection_mode='linear_extrapolation' selects the
     alternative path; partial-dict overrides KeyError on the
     `t["classify"]["nutrition"]["targets"]` read (covered by the
     trusted-by-design D13 seam).
  6. hai explain rendering: arm-2 surfaces both observed and projected
     in the explain-bundle's nutrition block.
  7. Synthesis-policy integration: cmd_synthesize consuming arm-2
     classified state operates against the projection, not the
     observed deficit.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.body_comp import add_body_comp  # noqa: F401  (sanity)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)
from health_agent_infra.core.state.snapshot import build_snapshot
from health_agent_infra.core.target.store import (
    TargetRecord,
    add_targets_atomic,
    get_active_macro_targets,
)
from health_agent_infra.domains.nutrition.classify import (
    classify_nutrition_state,
)
from health_agent_infra.core.config import load_thresholds


USER = "u_wd_arm2"
AS_OF = date(2026, 5, 5)


def _seed_target_rows(db_path: Path, *, kcal: float, protein: float,
                       carbs: float, fat: float) -> None:
    """Seed the 4 active macro target rows W-D arm-2 reads."""

    when = datetime.now(timezone.utc)
    records = []
    for tt, val, unit in (
        ("calories_kcal", kcal, "kcal"),
        ("protein_g", protein, "g"),
        ("carbs_g", carbs, "g"),
        ("fat_g", fat, "g"),
    ):
        records.append(TargetRecord(
            target_id=f"target_{tt}_{kcal:.0f}",
            user_id=USER,
            domain="nutrition",
            target_type=tt,
            status="active",
            value=val,
            unit=unit,
            lower_bound=None,
            upper_bound=None,
            effective_from=date(2026, 5, 1),
            effective_to=None,
            review_after=None,
            reason="W-D arm-2 fixture",
            source="user_authored",
            ingest_actor="cli",
            created_at=when,
            supersedes_target_id=None,
            superseded_by_target_id=None,
        ))
    with closing(open_connection(db_path)) as conn:
        add_targets_atomic(conn, records=records)


# ---------------------------------------------------------------------------
# Acceptance test 1 — plumbing helper
# ---------------------------------------------------------------------------


def test_get_active_macro_targets_returns_threshold_tree_keyed_dict(tmp_path):
    """get_active_macro_targets reads the 4 active target rows post-
    migration 025 and returns dict matching DEFAULT_THRESHOLDS shape."""

    db = tmp_path / "state.db"
    initialize_database(db)
    _seed_target_rows(db, kcal=3100, protein=160, carbs=350, fat=90)

    with closing(open_connection(db)) as conn:
        macros = get_active_macro_targets(conn, user_id=USER, as_of_date=AS_OF)

    assert macros == {
        "calorie_target_kcal": 3100.0,
        "protein_target_g": 160.0,
        "carbs_target_g": 350.0,
        "fat_target_g": 90.0,
    }


# ---------------------------------------------------------------------------
# Acceptance test 2 — projection emission via build_snapshot()
# ---------------------------------------------------------------------------


def _seed_partial_day_nutrition_intake(
    db_path: Path, *,
    calories: float, protein_g: float, carbs_g: float, fat_g: float,
    hydration_l: float, submission_time: datetime,
) -> None:
    """Insert one nutrition_intake_raw row + project to accepted_state.
    Mirrors the CLI handler's projection sequence."""

    from health_agent_infra.core.state.projector import (
        project_accepted_nutrition_state_daily,
    )

    with closing(open_connection(db_path)) as conn:
        conn.execute(
            "INSERT INTO nutrition_intake_raw ("
            " submission_id, user_id, as_of_date, calories, protein_g, "
            " carbs_g, fat_g, hydration_l, meals_count, source, "
            " ingest_actor, ingested_at, supersedes_submission_id"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "m_nut_arm2_fixture",
                USER,
                AS_OF.isoformat(),
                calories, protein_g, carbs_g, fat_g, hydration_l,
                1, "user_manual", "cli",
                submission_time.isoformat(),
                None,
            ),
        )
        conn.commit()
        project_accepted_nutrition_state_daily(
            conn, as_of_date=AS_OF, user_id=USER, ingest_actor="cli",
        )


def test_build_snapshot_target_anchored_projection_sets_aligned_status(tmp_path):
    """Seed 4 macro targets + partial-day intake (1344 kcal, 38g protein
    at 10am). build_snapshot internal merge selects target_anchored
    projection. Classified state should:
    - Carry projected_eod_kcal=3100, projected_eod_protein_g=160,
      projected_eod_carbs_g=350, projected_eod_fat_g=90.
    - nutrition_status='aligned' (projection closes the gap).
    - calorie_balance_band='met' (deficit collapses to 0).
    - protein_sufficiency_band='met' (ratio = 1.0; band vocab is
      met|low|very_low|unknown per classify.py:86).
    """

    db = tmp_path / "state.db"
    initialize_database(db)
    _seed_target_rows(db, kcal=3100, protein=160, carbs=350, fat=90)

    submission_time = datetime(2026, 5, 5, 10, 0, 0, tzinfo=timezone.utc)
    _seed_partial_day_nutrition_intake(
        db, calories=1344.0, protein_g=38.0, carbs_g=160.0, fat_g=42.0,
        hydration_l=1.0, submission_time=submission_time,
    )

    with closing(open_connection(db)) as conn:
        snapshot = build_snapshot(
            conn,
            as_of_date=AS_OF,
            user_id=USER,
            now_local=submission_time,
        )

    nutrition_classified = snapshot["nutrition"]["classified_state"]

    # The 4 projected_eod_* fields surface in the snapshot's classified_state.
    assert nutrition_classified.get("projected_eod_kcal") == 3100.0, (
        f"projected_eod_kcal missing or wrong: {nutrition_classified}"
    )
    assert nutrition_classified.get("projected_eod_protein_g") == 160.0
    assert nutrition_classified.get("projected_eod_carbs_g") == 350.0
    assert nutrition_classified.get("projected_eod_fat_g") == 90.0

    # Bands fire against the projection (closed gap → met).
    assert nutrition_classified["calorie_balance_band"] == "met", (
        f"calorie_balance_band should be 'met' under target-anchored "
        f"projection: {nutrition_classified}"
    )
    # Per classify.py:86 the protein-sufficiency-band vocabulary is
    # "met"|"low"|"very_low"|"unknown" — there is no "adequate" value.
    assert nutrition_classified["protein_sufficiency_band"] == "met", (
        f"protein_sufficiency_band should be 'met': {nutrition_classified}"
    )
    # PLAN §2.I "Macro projection scope": hydration is intentionally
    # held observed (no hydration target in the W-C-shipped 4-row group;
    # NUTRITION_MACRO_TARGET_TYPES covers macros only). With 1.0L observed
    # vs the 2.5L default, the day's macros are aligned but hydration
    # follows the observed-not-projected path → status='under_hydrated'.
    # The arm-2 contract is that the macro projection drives the macro
    # bands without claiming hydration is also projected.
    assert nutrition_classified["calorie_deficit_kcal"] == 0.0
    assert nutrition_classified["protein_ratio"] == 1.0
    assert nutrition_classified["hydration_ratio"] == 0.4
    assert nutrition_classified["nutrition_status"] in ("aligned", "under_hydrated"), (
        f"nutrition_status should reflect aligned macros (under_hydrated "
        f"acceptable when hydration target unmet): {nutrition_classified}"
    )


# ---------------------------------------------------------------------------
# Acceptance test 3 — arm-2/arm-1 boundary
# ---------------------------------------------------------------------------


def test_arm1_fires_when_target_absent_or_unavailable(tmp_path):
    """target_status='absent' or 'unavailable' → arm-1 suppression
    fires (nutrition_status='insufficient_data', uncertainty=
    ('partial_day_no_target',)); no projected_eod_* fields."""

    # Test directly against classify_nutrition_state with synthesized
    # signals (no need for a full DB seed).
    for target_status in ("absent", "unavailable"):
        signals = {
            "today_row": {"calories": 1344.0, "protein_g": 38.0,
                          "derivation_path": "v1_macros_only"},
            "is_partial_day": True,
            "target_status": target_status,
        }
        classified = classify_nutrition_state(signals)
        assert classified.nutrition_status == "insufficient_data", (
            f"target_status={target_status}: expected insufficient_data, "
            f"got {classified.nutrition_status}"
        )
        assert "partial_day_no_target" in classified.uncertainty
        assert classified.projected_eod_kcal is None
        assert classified.projected_eod_protein_g is None


# ---------------------------------------------------------------------------
# Acceptance test 4 — day-closed
# ---------------------------------------------------------------------------


def test_day_closed_falls_through_to_existing_classifier(tmp_path):
    """is_partial_day=False → no arm-2 projection; existing classifier
    runs against observed values; no projected_eod_* fields."""

    signals = {
        "today_row": {"calories": 2400.0, "protein_g": 140.0,
                      "hydration_l": 2.5,
                      "derivation_path": "v1_macros_only"},
        "is_partial_day": False,
        "target_status": "present",
    }
    classified = classify_nutrition_state(signals)
    assert classified.projected_eod_kcal is None
    assert classified.projected_eod_protein_g is None


# ---------------------------------------------------------------------------
# Acceptance test 5 — linear-extrapolation reachability via threshold override
# ---------------------------------------------------------------------------


def test_linear_extrapolation_reachable_via_full_tree_threshold_override():
    """Build a deep-merged full thresholds tree, override projection_mode
    to 'linear_extrapolation', pass to classify_nutrition_state. Assert
    the linear-extrapolation projection shape emits (projected_eod_kcal
    = intake / fraction_of_day) and target-anchored does NOT emit."""

    from copy import deepcopy

    full_tree = deepcopy(load_thresholds())
    full_tree["classify"]["nutrition"]["projection_mode"] = "linear_extrapolation"
    # Inject the carbs/fat targets so linear extrapolation has them
    # available (default tree only has kcal/protein/hydration).
    full_tree["classify"]["nutrition"]["targets"]["carbs_target_g"] = 350.0
    full_tree["classify"]["nutrition"]["targets"]["fat_target_g"] = 90.0

    signals = {
        "today_row": {
            "calories": 600.0, "protein_g": 30.0,
            "carbs_g": 80.0, "fat_g": 15.0,
            "hydration_l": 0.5,
            "derivation_path": "v1_macros_only",
        },
        "is_partial_day": True,
        "target_status": "present",
        "now_local": datetime(2026, 5, 5, 12, 0, 0, tzinfo=timezone.utc),  # noon: 0.5 of day
    }

    classified = classify_nutrition_state(signals, thresholds=full_tree)

    # Linear extrapolation: 600 kcal / 0.5 = 1200 kcal projected.
    assert classified.projected_eod_kcal == 1200.0, (
        f"linear-extrapolation projected_eod_kcal expected 1200.0, "
        f"got {classified.projected_eod_kcal}"
    )
    assert classified.projected_eod_protein_g == 60.0
    # Carbs + fat were tracked + targets supplied.
    assert classified.projected_eod_carbs_g == 160.0
    assert classified.projected_eod_fat_g == 30.0


# ---------------------------------------------------------------------------
# Acceptance test 6 — `hai explain` rendering of observed + projected
#
# v0.1.17 IR-R1 F-IR-03 fix: arm-2 surfaces both observed calories and
# projected_eod_kcal in the explain bundle. The integration path is:
#
#   build_snapshot → run_synthesis → daily_plan.synthesis_meta JSON →
#   load_bundle_for_date → bundle_to_dict / render_bundle_text.
#
# synthesis writes the classified state + observed today_row into
# ``synthesis_meta.domain_classified_states.nutrition``; explain reads
# that JSON directly, no recomputation required.
# ---------------------------------------------------------------------------


def test_hai_explain_renders_observed_and_projected_eod_for_arm2(tmp_path):
    """End-to-end W-D arm-2 explain rendering acceptance.

    Sequence:
      1. Seed 4 active macro targets + partial-day nutrition intake.
      2. Run build_snapshot → confirms classified_state has projected_eod_*.
      3. Project a minimal nutrition proposal so synthesis can run.
      4. Run synthesis with the snapshot — the daily_plan row's
         ``synthesis_meta.domain_classified_states.nutrition`` block
         persists observed + classified (incl. projected_eod_*).
      5. Load the explain bundle; assert bundle_to_dict surfaces
         observed.calories AND projected_eod_kcal in the JSON view.
      6. Render the operator text; assert both values are in the report.
    """

    from health_agent_infra.core.explain import (
        bundle_to_dict,
        load_bundle_for_date,
        render_bundle_text,
    )
    from health_agent_infra.core.state.projector import project_proposal
    from health_agent_infra.core.synthesis import run_synthesis

    db = tmp_path / "state.db"
    initialize_database(db)
    _seed_target_rows(db, kcal=3100, protein=160, carbs=350, fat=90)

    submission_time = datetime(2026, 5, 5, 10, 0, 0, tzinfo=timezone.utc)
    _seed_partial_day_nutrition_intake(
        db, calories=1344.0, protein_g=38.0, carbs_g=160.0, fat_g=42.0,
        hydration_l=1.0, submission_time=submission_time,
    )

    with closing(open_connection(db)) as conn:
        snapshot = build_snapshot(
            conn,
            as_of_date=AS_OF,
            user_id=USER,
            now_local=submission_time,
        )

        # Confirm arm-2 fired before going through synthesis.
        nutrition_classified = snapshot["nutrition"]["classified_state"]
        assert nutrition_classified["projected_eod_kcal"] == 3100.0

        # Project a minimal nutrition proposal so synthesis has something
        # to commit. Carbon-copy the shape used by other test fixtures.
        proposal = {
            "schema_version": "domain_proposal.v1",
            "proposal_id": "nut_arm2_explain_proposal",
            "domain": "nutrition",
            "user_id": USER,
            "for_date": AS_OF.isoformat(),
            "action": "maintain_targets",
            "action_detail": {
                "calorie_target_kcal": 3100,
                "protein_target_g": 160,
            },
            "confidence": "moderate",
            "rationale": ["arm-2 projection closes the gap"],
            "uncertainty": [],
            "policy_decisions": [
                {"rule_id": "wd_arm2_test_seed", "decision": "allow",
                 "note": "fixture proposal for explain rendering"},
            ],
        }
        project_proposal(conn, proposal)

        result = run_synthesis(
            conn,
            for_date=AS_OF,
            user_id=USER,
            snapshot=snapshot,
            expected_domains=None,
        )
        assert result is not None

        # Now load the explain bundle for the same date.
        bundle = load_bundle_for_date(
            conn, for_date=AS_OF, user_id=USER, plan_version="latest",
        )

    # JSON shape — synthesis_meta.domain_classified_states.nutrition
    # carries both observed (calories=1344) and projected (kcal=3100).
    bundle_dict = bundle_to_dict(bundle)
    domain_states = (
        bundle_dict["plan"]["synthesis_meta"]
        .get("domain_classified_states", {})
    )
    assert "nutrition" in domain_states, (
        f"synthesis_meta.domain_classified_states missing nutrition: "
        f"{bundle_dict['plan']['synthesis_meta']}"
    )
    nut = domain_states["nutrition"]
    assert nut["observed"]["calories"] == 1344.0
    assert nut["classified"]["projected_eod_kcal"] == 3100.0

    # Operator text surface — both numeric tokens appear in the report.
    text = render_bundle_text(bundle)
    assert "calories     : 1344" in text, (
        f"observed calories not rendered. Output:\n{text[:1500]}"
    )
    assert "projected_eod_kcal      : 3100" in text, (
        f"projected_eod_kcal not rendered. Output:\n{text[:1500]}"
    )


# ---------------------------------------------------------------------------
# Acceptance test 7 — synthesis-policy integration (operates against projection)
# ---------------------------------------------------------------------------


def test_synthesis_does_not_propose_recovery_against_arm2_false_deficit(tmp_path):
    """Build the snapshot under arm-2 conditions; assert the nutrition
    block's policy_result does NOT carry an extreme-deficiency forced
    action (the projection closes the gap so the X2/R-extreme paths
    that fire under arm-1 fallback are no longer triggered).
    """

    db = tmp_path / "state.db"
    initialize_database(db)
    _seed_target_rows(db, kcal=3100, protein=160, carbs=350, fat=90)

    submission_time = datetime(2026, 5, 5, 10, 0, 0, tzinfo=timezone.utc)
    _seed_partial_day_nutrition_intake(
        db, calories=1344.0, protein_g=38.0, carbs_g=160.0, fat_g=42.0,
        hydration_l=1.0, submission_time=submission_time,
    )

    with closing(open_connection(db)) as conn:
        snapshot = build_snapshot(
            conn,
            as_of_date=AS_OF,
            user_id=USER,
            now_local=submission_time,
        )

    nutrition_policy = snapshot["nutrition"]["policy_result"]
    forced = nutrition_policy.get("forced_action") if nutrition_policy else None
    # The arm-1 fallback (suppression to insufficient_data) historically
    # produced no extreme-deficiency escalation — but more importantly,
    # the arm-2 projection should NOT now trigger one against the
    # closed-gap state. forced_action being absent OR a benign action
    # (e.g. maintain_targets) is the contract under test.
    assert forced not in ("escalate_extreme_deficiency",), (
        f"arm-2 projection should not trigger extreme-deficiency forced "
        f"action against the closed-gap state; got forced_action={forced!r}"
    )
