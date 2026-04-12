from __future__ import annotations

import json
from pathlib import Path
import unittest

from health_model.manual_logging import (
    build_exercise_set_manual_log_entry,
    build_hydration_input_event,
    build_hydration_manual_log_entry,
    build_manual_logging_bundle,
    build_manual_source_artifact,
    build_nutrition_text_note_manual_log_entry,
    build_simple_gym_set_manual_log_entry,
)
from health_model.shared_input_backbone import validate_shared_input_bundle


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "manual_logging"


class ManualLoggingTest(unittest.TestCase):
    def test_nutrition_text_note_fixture_enters_canonical_backbone_cleanly(self) -> None:
        bundle = _load_fixture("nutrition_text_note_bundle.json")
        result = validate_shared_input_bundle(bundle)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.schema_issues, [])
        self.assertEqual(result.semantic_issues, [])
        self.assertEqual(bundle["manual_log_entries"][0]["completeness_state"], "complete")
        self.assertEqual(bundle["manual_log_entries"][0]["payload"]["notes"], "Turkey sandwich, yogurt, and an apple. Portions are approximate.")

    def test_hydration_fixture_enters_canonical_backbone_cleanly(self) -> None:
        bundle = _load_fixture("hydration_bundle.json")
        result = validate_shared_input_bundle(bundle)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.schema_issues, [])
        self.assertEqual(result.semantic_issues, [])
        self.assertEqual(bundle["manual_log_entries"][0]["payload"]["beverage_type"], "water")
        self.assertEqual(bundle["input_events"][0]["provenance"]["supporting_refs"], ["manual_log_entry:manual_01JQZHMANUALH1"])

    def test_simple_gym_set_fixture_enters_canonical_backbone_cleanly(self) -> None:
        bundle = _load_fixture("simple_gym_set_bundle.json")
        result = validate_shared_input_bundle(bundle)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.schema_issues, [])
        self.assertEqual(result.semantic_issues, [])
        self.assertEqual(bundle["manual_log_entries"][0]["payload"]["reps"], 5)
        self.assertEqual(bundle["manual_log_entries"][0]["payload"]["weight_kg"], 80)

    def test_builders_cover_bounded_manual_input_slice(self) -> None:
        artifact = build_manual_source_artifact(
            artifact_id="artifact_01JQZMANUALA1",
            user_id="user_dom",
            source_name="manual_day_log",
            collected_at="2026-04-10T18:42:00+01:00",
            ingested_at="2026-04-10T18:42:03+01:00",
            raw_location="healthlab://manual/day/2026-04-10",
            parser_version="manual-form@0.1.0",
        )
        nutrition_entry = build_nutrition_text_note_manual_log_entry(
            entry_id="manual_01JQZNUTEA001",
            user_id="user_dom",
            date="2026-04-10",
            source_artifact_id=artifact["artifact_id"],
            note_text="Chicken wrap and crisps after a late meeting.",
            meal_label="dinner",
            completeness_state="complete",
            confidence_score=0.99,
        )
        hydration_entry = build_hydration_manual_log_entry(
            entry_id="manual_01JQZHYDRATEA1",
            user_id="user_dom",
            date="2026-04-10",
            source_artifact_id=artifact["artifact_id"],
            amount_ml=600,
            beverage_type="water",
            completeness_state="complete",
            confidence_score=0.99,
        )
        gym_set_entry = build_simple_gym_set_manual_log_entry(
            entry_id="manual_01JQZSETA001",
            user_id="user_dom",
            date="2026-04-10",
            source_artifact_id=artifact["artifact_id"],
            exercise_name="front squat",
            set_index=1,
            reps=5,
            weight_kg=80,
            completeness_state="complete",
            confidence_score=0.99,
        )
        hydration_event = build_hydration_input_event(
            event_id="event_01JQZHYDEVENT1",
            source_record_id="manual_hydration_2026-04-10_1",
            manual_entry=hydration_entry,
            artifact=artifact,
        )
        bundle = build_manual_logging_bundle(
            source_artifact=artifact,
            manual_log_entries=[nutrition_entry, hydration_entry, gym_set_entry],
            input_events=[hydration_event],
        )
        result = validate_shared_input_bundle(bundle)

        self.assertTrue(result.is_valid)
        self.assertEqual(bundle["manual_log_entries"][0]["log_type"], "meal")
        self.assertEqual(bundle["manual_log_entries"][2]["payload"]["weight_kg"], 80)
        self.assertEqual(bundle["input_events"][0]["metric_name"], "hydration_amount_ml")

    def test_complete_exercise_set_requires_reps_for_honest_completeness(self) -> None:
        artifact = build_manual_source_artifact(
            artifact_id="artifact_01JQZMANUALA2",
            user_id="user_dom",
            source_name="manual_gym_hydration_log",
            collected_at="2026-04-10T18:42:00+01:00",
            ingested_at="2026-04-10T18:42:03+01:00",
            raw_location="healthlab://manual/gym-hydration/2026-04-10",
        )
        incomplete_gym_set = build_exercise_set_manual_log_entry(
            entry_id="manual_01JQZSETA002",
            user_id="user_dom",
            date="2026-04-10",
            source_artifact_id=artifact["artifact_id"],
            exercise_name="front squat",
            set_index=2,
            weight_kg=80,
            completeness_state="complete",
            confidence_score=0.99,
        )
        bundle = build_manual_logging_bundle(
            source_artifact=artifact,
            manual_log_entries=[incomplete_gym_set],
        )

        result = validate_shared_input_bundle(bundle)

        self.assertFalse(result.is_valid)
        self.assertIn("manual_completeness_mismatch", {issue.code for issue in result.semantic_issues})

    def test_complete_meal_requires_notes_or_items_for_honest_completeness(self) -> None:
        artifact = build_manual_source_artifact(
            artifact_id="artifact_01JQZMANUALA3",
            user_id="user_dom",
            source_name="manual_nutrition_log",
            collected_at="2026-04-10T12:31:00+01:00",
            ingested_at="2026-04-10T12:31:04+01:00",
            raw_location="healthlab://manual/nutrition/2026-04-10",
        )
        incomplete_meal = {
            "entry_id": "manual_01JQZMEALA001",
            "user_id": "user_dom",
            "date": "2026-04-10",
            "log_type": "meal",
            "payload": {"meal_label": "lunch", "estimated": True},
            "source_artifact_id": artifact["artifact_id"],
            "completeness_state": "complete",
            "confidence_label": "high",
            "confidence_score": 0.99,
        }
        bundle = build_manual_logging_bundle(
            source_artifact=artifact,
            manual_log_entries=[incomplete_meal],
        )

        result = validate_shared_input_bundle(bundle)

        self.assertFalse(result.is_valid)
        self.assertIn("manual_completeness_mismatch", {issue.code for issue in result.semantic_issues})


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_DIR / name).read_text())


if __name__ == "__main__":
    unittest.main()
