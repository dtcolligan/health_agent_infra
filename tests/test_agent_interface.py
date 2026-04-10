from __future__ import annotations

import json
import unittest
from pathlib import Path

from health_model.agent_interface import (
    build_daily_context,
    merge_bundle_fragments,
    submit_hydration_log,
    submit_gym_set,
    submit_nutrition_text_note,
    validate_bundle,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readable_daily_context"


class AgentInterfaceTest(unittest.TestCase):
    def test_submit_hydration_log_returns_canonical_fragment_with_linked_provenance(self) -> None:
        response = submit_hydration_log(
            user_id="user_dom",
            date="2026-04-10",
            amount_ml=600,
            beverage_type="water",
            completeness_state="complete",
            collected_at="2026-04-10T18:42:00+01:00",
            ingested_at="2026-04-10T18:42:03+01:00",
            raw_location="healthlab://manual/hydration/2026-04-10",
            confidence_score=0.99,
            notes="Post-training bottle.",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["entry_kind"], "manual_log_entry")
        self.assertTrue(response["validation"]["is_valid"])
        self.assertIsNone(response["error"])
        self.assertEqual(response["artifact"]["source_type"], "manual")
        self.assertEqual(response["entry"]["source_artifact_id"], response["artifact"]["artifact_id"])
        self.assertEqual(response["provenance"]["artifact_id"], response["artifact"]["artifact_id"])
        self.assertEqual(response["provenance"]["entry_id"], response["entry"]["entry_id"])
        self.assertEqual(response["provenance"]["event_id"], response["derived_events"][0]["event_id"])
        self.assertEqual(
            response["derived_events"][0]["provenance"]["supporting_refs"],
            [f"manual_log_entry:{response['entry']['entry_id']}"],
        )
        self.assertEqual(
            response["derived_events"][0]["provenance"]["derivation_method"],
            "manual_form_normalization",
        )
        self.assertEqual(response["bundle_fragment"]["manual_log_entries"], [response["entry"]])
        self.assertEqual(response["bundle_fragment"]["input_events"], response["derived_events"])

    def test_submit_nutrition_text_note_fails_closed_on_invalid_bundle_fragment(self) -> None:
        response = submit_nutrition_text_note(
            user_id="user_dom",
            date="2026-04-10",
            note_text="",
            meal_label="lunch",
            estimated=True,
            completeness_state="complete",
            collected_at="2026-04-10T12:31:00+01:00",
            ingested_at="2026-04-10T12:31:04+01:00",
            raw_location="healthlab://manual/nutrition/2026-04-10",
            confidence_score=0.99,
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "invalid_bundle_fragment")
        self.assertFalse(response["validation"]["is_valid"])
        self.assertIn(
            "invalid_manual_payload_shape",
            {issue["code"] for issue in response["validation"]["semantic_issues"]},
        )

    def test_build_daily_context_preserves_truth_statuses_and_day_scoping(self) -> None:
        bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        context = build_daily_context(bundle=bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(context["artifact_type"], "agent_readable_daily_context")
        self.assertEqual(
            context["generated_from"]["source_artifact_ids"],
            [
                "artifact_manual_20260409",
                "artifact_voice_20260409",
                "artifact_wearable_20260409",
            ],
        )
        self.assertNotIn("artifact_manual_20260408", context["generated_from"]["source_artifact_ids"])
        self.assertNotIn("artifact_voice_20260408", context["generated_from"]["source_artifact_ids"])
        self.assertNotIn("artifact_wearable_20260408", context["generated_from"]["source_artifact_ids"])

        statuses = {signal["status"] for signal in context["explicit_grounding"]["signals"]}
        self.assertEqual(statuses, {"grounded", "inferred", "missing", "conflicted"})
        self.assertIn("conflicting_passive_activity", {conflict["code"] for conflict in context["conflicts"]})
        self.assertIn("missing_subjective_sleep_quality", {gap["code"] for gap in context["important_gaps"]})

    def test_validate_bundle_reports_read_only_validation_shape(self) -> None:
        bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        result = validate_bundle(bundle=bundle)

        self.assertTrue(result["ok"])
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["schema_issues"], [])
        self.assertEqual(result["semantic_issues"], [])

    def test_roundtrip_same_day_interface_fragments_merge_into_daily_context_without_cross_day_leakage(self) -> None:
        bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        same_day_hydration = submit_hydration_log(
            user_id="user_1",
            date="2026-04-09",
            amount_ml=750,
            beverage_type="water",
            completeness_state="complete",
            collected_at="2026-04-09T18:20:00+01:00",
            ingested_at="2026-04-09T18:20:03+01:00",
            raw_location="healthlab://manual/hydration/2026-04-09/evening",
            confidence_score=0.98,
            notes="Evening refill after training.",
        )
        same_day_meal = submit_nutrition_text_note(
            user_id="user_1",
            date="2026-04-09",
            note_text="Chicken rice bowl and fruit after run.",
            meal_label="dinner",
            estimated=True,
            completeness_state="complete",
            collected_at="2026-04-09T20:10:00+01:00",
            ingested_at="2026-04-09T20:10:04+01:00",
            raw_location="healthlab://manual/nutrition/2026-04-09/dinner",
            confidence_score=0.94,
        )
        same_day_gym = submit_gym_set(
            user_id="user_1",
            date="2026-04-09",
            exercise_name="Back Squat",
            set_index=2,
            reps=5,
            weight_kg=110.0,
            completeness_state="complete",
            collected_at="2026-04-09T17:45:00+01:00",
            ingested_at="2026-04-09T17:45:02+01:00",
            raw_location="healthlab://manual/gym/2026-04-09/back-squat-2",
            confidence_score=0.96,
        )
        wrong_day_hydration = submit_hydration_log(
            user_id="user_1",
            date="2026-04-08",
            amount_ml=300,
            beverage_type="water",
            completeness_state="complete",
            collected_at="2026-04-08T21:00:00+01:00",
            ingested_at="2026-04-08T21:00:02+01:00",
            raw_location="healthlab://manual/hydration/2026-04-08/night",
            confidence_score=0.93,
            notes="Wrong-day control fragment.",
        )

        for response in (same_day_hydration, same_day_meal, same_day_gym, wrong_day_hydration):
            self.assertTrue(response["ok"], msg=response)
            self.assertTrue(response["validation"]["is_valid"], msg=response["validation"])

        merged_bundle = merge_bundle_fragments(
            bundle,
            same_day_hydration["bundle_fragment"],
            same_day_meal["bundle_fragment"],
            same_day_gym["bundle_fragment"],
            wrong_day_hydration["bundle_fragment"],
        )

        validation = validate_bundle(bundle=merged_bundle)
        self.assertTrue(validation["is_valid"], msg=validation)

        context = build_daily_context(bundle=merged_bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(context["artifact_type"], "agent_readable_daily_context")
        self.assertIn(same_day_gym["artifact"]["artifact_id"], context["generated_from"]["source_artifact_ids"])
        self.assertIn(same_day_hydration["artifact"]["artifact_id"], context["generated_from"]["source_artifact_ids"])
        self.assertIn(same_day_meal["artifact"]["artifact_id"], context["generated_from"]["source_artifact_ids"])
        self.assertNotIn(
            wrong_day_hydration["artifact"]["artifact_id"],
            context["generated_from"]["source_artifact_ids"],
        )
        self.assertIn(
            same_day_hydration["derived_events"][0]["event_id"],
            context["generated_from"]["input_event_ids"],
        )
        self.assertNotIn(
            wrong_day_hydration["derived_events"][0]["event_id"],
            context["generated_from"]["input_event_ids"],
        )
        self.assertIn(same_day_hydration["entry"]["entry_id"], context["generated_from"]["manual_log_entry_ids"])
        self.assertIn(same_day_meal["entry"]["entry_id"], context["generated_from"]["manual_log_entry_ids"])
        self.assertIn(same_day_gym["entry"]["entry_id"], context["generated_from"]["manual_log_entry_ids"])
        self.assertNotIn(
            wrong_day_hydration["entry"]["entry_id"],
            context["generated_from"]["manual_log_entry_ids"],
        )

        statuses = {signal["status"] for signal in context["explicit_grounding"]["signals"]}
        self.assertEqual(statuses, {"grounded", "inferred", "missing", "conflicted"})

        nutrition_signal = next(
            signal
            for signal in context["explicit_grounding"]["signals"]
            if signal["domain"] == "nutrition" and signal["signal_key"] == "manual_meal_logs"
        )
        hydration_signal = next(
            signal
            for signal in context["explicit_grounding"]["signals"]
            if signal["domain"] == "hydration" and signal["signal_key"] == "hydration_intake_ml"
        )
        self.assertEqual(nutrition_signal["status"], "grounded")
        self.assertEqual(nutrition_signal["evidence_refs"], [same_day_meal["entry"]["entry_id"]])
        self.assertEqual(hydration_signal["status"], "grounded")
        self.assertEqual(
            hydration_signal["evidence_refs"],
            [
                same_day_hydration["derived_events"][0]["event_id"],
                same_day_hydration["entry"]["entry_id"],
            ],
        )

    def test_duplicate_same_day_hydration_replay_does_not_inflate_daily_total(self) -> None:
        bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        original = submit_hydration_log(
            user_id="user_1",
            date="2026-04-09",
            amount_ml=750,
            beverage_type="water",
            completeness_state="complete",
            collected_at="2026-04-09T18:20:00+01:00",
            ingested_at="2026-04-09T18:20:03+01:00",
            raw_location="healthlab://manual/hydration/2026-04-09/evening",
            confidence_score=0.98,
            notes="Evening refill after training.",
        )
        replay = submit_hydration_log(
            user_id="user_1",
            date="2026-04-09",
            amount_ml=750,
            beverage_type="water",
            completeness_state="complete",
            collected_at="2026-04-09T18:20:00+01:00",
            ingested_at="2026-04-09T18:25:03+01:00",
            raw_location="healthlab://manual/hydration/2026-04-09/evening",
            confidence_score=0.98,
            notes="Evening refill after training.",
        )

        for response in (original, replay):
            self.assertTrue(response["ok"], msg=response)
            self.assertTrue(response["validation"]["is_valid"], msg=response["validation"])

        merged_bundle = merge_bundle_fragments(
            bundle,
            original["bundle_fragment"],
            replay["bundle_fragment"],
        )
        context = build_daily_context(bundle=merged_bundle, user_id="user_1", date="2026-04-09")

        hydration_signal = next(
            signal
            for signal in context["explicit_grounding"]["signals"]
            if signal["domain"] == "hydration" and signal["signal_key"] == "hydration_intake_ml"
        )

        self.assertEqual(hydration_signal["status"], "grounded")
        self.assertEqual(hydration_signal["value"]["total_amount_ml"], 750.0)
        self.assertEqual(hydration_signal["value"]["log_count"], 1)
        self.assertEqual(
            hydration_signal["evidence_refs"],
            [replay["derived_events"][0]["event_id"], replay["entry"]["entry_id"]],
        )

    def test_distinct_same_day_hydration_logs_still_sum_correctly(self) -> None:
        bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        first = submit_hydration_log(
            user_id="user_1",
            date="2026-04-09",
            amount_ml=500,
            beverage_type="water",
            completeness_state="complete",
            collected_at="2026-04-09T09:00:00+01:00",
            ingested_at="2026-04-09T09:00:03+01:00",
            raw_location="healthlab://manual/hydration/2026-04-09/morning",
            confidence_score=0.97,
            notes="Morning bottle.",
        )
        second = submit_hydration_log(
            user_id="user_1",
            date="2026-04-09",
            amount_ml=750,
            beverage_type="water",
            completeness_state="complete",
            collected_at="2026-04-09T18:20:00+01:00",
            ingested_at="2026-04-09T18:20:03+01:00",
            raw_location="healthlab://manual/hydration/2026-04-09/evening",
            confidence_score=0.98,
            notes="Evening refill after training.",
        )

        for response in (first, second):
            self.assertTrue(response["ok"], msg=response)
            self.assertTrue(response["validation"]["is_valid"], msg=response["validation"])

        merged_bundle = merge_bundle_fragments(
            bundle,
            first["bundle_fragment"],
            second["bundle_fragment"],
        )
        context = build_daily_context(bundle=merged_bundle, user_id="user_1", date="2026-04-09")

        hydration_signal = next(
            signal
            for signal in context["explicit_grounding"]["signals"]
            if signal["domain"] == "hydration" and signal["signal_key"] == "hydration_intake_ml"
        )

        self.assertEqual(hydration_signal["status"], "grounded")
        self.assertEqual(hydration_signal["value"]["total_amount_ml"], 1250.0)
        self.assertEqual(hydration_signal["value"]["log_count"], 2)
        self.assertEqual(
            hydration_signal["evidence_refs"],
            sorted(
                [
                    first["derived_events"][0]["event_id"],
                    first["entry"]["entry_id"],
                    second["derived_events"][0]["event_id"],
                    second["entry"]["entry_id"],
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
