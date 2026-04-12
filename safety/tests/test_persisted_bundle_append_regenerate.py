from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from health_model import build_daily_context_artifact as daily_context_artifact_module

from health_model.agent_interface import (
    append_fragment_and_regenerate_daily_context,
    load_persisted_bundle,
    submit_gym_set,
    submit_hydration_log,
    submit_nutrition_text_note,
    write_persisted_bundle,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readable_daily_context"


class PersistedBundleAppendRegenerateTest(unittest.TestCase):
    def test_atomic_entrypoint_appends_same_day_fragment_and_regenerates_latest_artifact(self) -> None:
        base_bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        deterministic_ids = iter(
            [
                "artifact_hydration_20260409",
                "manual_hydration_20260409",
                "event_hydration_20260409",
                "artifact_meal_20260409",
                "manual_meal_20260409",
                "event_meal_20260409",
                "artifact_hydration_20260408",
                "manual_hydration_20260408",
                "event_hydration_20260408",
                "artifact_invalid_meal_20260409",
                "manual_invalid_meal_20260409",
                "event_invalid_meal_20260409",
                "artifact_gym_20260409",
                "manual_gym_20260409",
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "health_model.agent_interface._new_id", side_effect=lambda prefix: next(deterministic_ids)
        ):
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            write_persisted_bundle(bundle_path=str(bundle_path), bundle=base_bundle)

            hydration = submit_hydration_log(
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
            meal = submit_nutrition_text_note(
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
            wrong_day = submit_hydration_log(
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
            invalid = submit_nutrition_text_note(
                user_id="user_1",
                date="2026-04-09",
                note_text="",
                meal_label="lunch",
                estimated=True,
                completeness_state="complete",
                collected_at="2026-04-09T12:31:00+01:00",
                ingested_at="2026-04-09T12:31:04+01:00",
                raw_location="healthlab://manual/nutrition/2026-04-09/lunch",
                confidence_score=0.99,
            )

            hydration_result = append_fragment_and_regenerate_daily_context(
                bundle_path=str(bundle_path),
                output_dir=str(health_dir),
                fragment=hydration["bundle_fragment"],
                user_id="user_1",
                date="2026-04-09",
            )
            meal_result = append_fragment_and_regenerate_daily_context(
                bundle_path=str(bundle_path),
                output_dir=str(health_dir),
                fragment=meal["bundle_fragment"],
                user_id="user_1",
                date="2026-04-09",
            )

            self.assertTrue(hydration_result["ok"], msg=hydration_result)
            self.assertTrue(meal_result["ok"], msg=meal_result)

            dated_path = health_dir / "agent_readable_daily_context_2026-04-09.json"
            latest_path = health_dir / "agent_readable_daily_context_latest.json"
            self.assertEqual(meal_result["bundle_path"], str(bundle_path))
            self.assertEqual(meal_result["dated_artifact_path"], str(dated_path))
            self.assertEqual(meal_result["latest_artifact_path"], str(latest_path))
            self.assertEqual(
                meal_result["accepted_provenance"],
                {
                    "source_artifact_ids": ["artifact_meal_20260409"],
                    "input_event_ids": [
                        "event_meal_20260409_meal_logged",
                        "event_meal_20260409_meal_estimated_flag",
                        "event_meal_20260409_meal_label",
                    ],
                    "subjective_entry_ids": [],
                    "manual_log_entry_ids": ["manual_meal_20260409"],
                },
            )
            self.assertTrue(dated_path.exists())
            self.assertTrue(latest_path.exists())

            persisted_bundle = load_persisted_bundle(bundle_path=str(bundle_path))
            persisted_manual_ids = {entry["entry_id"] for entry in persisted_bundle["manual_log_entries"]}
            self.assertIn("manual_hydration_20260409", persisted_manual_ids)
            self.assertIn("manual_meal_20260409", persisted_manual_ids)
            self.assertNotIn("manual_hydration_20260408", persisted_manual_ids)

            artifact = json.loads(dated_path.read_text())
            latest_artifact = json.loads(latest_path.read_text())
            self.assertEqual(artifact, latest_artifact)
            self.assertIn("artifact_hydration_20260409", artifact["generated_from"]["source_artifact_ids"])
            self.assertIn("artifact_meal_20260409", artifact["generated_from"]["source_artifact_ids"])
            self.assertNotIn("artifact_hydration_20260408", artifact["generated_from"]["source_artifact_ids"])
            self.assertIn("manual_hydration_20260409", artifact["generated_from"]["manual_log_entry_ids"])
            self.assertIn("manual_meal_20260409", artifact["generated_from"]["manual_log_entry_ids"])
            self.assertNotIn("manual_hydration_20260408", artifact["generated_from"]["manual_log_entry_ids"])

            nutrition_signal = next(
                signal
                for signal in artifact["explicit_grounding"]["signals"]
                if signal["domain"] == "nutrition" and signal["signal_key"] == "manual_meal_logs"
            )
            hydration_signal = next(
                signal
                for signal in artifact["explicit_grounding"]["signals"]
                if signal["domain"] == "hydration" and signal["signal_key"] == "hydration_intake_ml"
            )
            self.assertEqual(nutrition_signal["value"]["meal_labels"], ["dinner"])
            self.assertEqual(nutrition_signal["value"]["notes"], ["Chicken rice bowl and fruit after run."])
            self.assertEqual(hydration_signal["value"]["total_amount_ml"], 750.0)
            self.assertEqual(hydration_signal["value"]["beverage_types"], ["water"])

    def test_atomic_entrypoint_rejects_invalid_and_wrong_day_fragments_without_mutation(self) -> None:
        base_bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        deterministic_ids = iter(
            [
                "artifact_wrong_day_hydration_20260408",
                "manual_wrong_day_hydration_20260408",
                "event_wrong_day_hydration_20260408",
                "artifact_invalid_meal_20260409",
                "manual_invalid_meal_20260409",
                "event_invalid_meal_20260409",
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "health_model.agent_interface._new_id", side_effect=lambda prefix: next(deterministic_ids)
        ):
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            write_persisted_bundle(bundle_path=str(bundle_path), bundle=base_bundle)
            original_bundle_text = bundle_path.read_text()

            wrong_day = submit_hydration_log(
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
            invalid = submit_nutrition_text_note(
                user_id="user_1",
                date="2026-04-09",
                note_text="",
                meal_label="lunch",
                estimated=True,
                completeness_state="complete",
                collected_at="2026-04-09T12:31:00+01:00",
                ingested_at="2026-04-09T12:31:04+01:00",
                raw_location="healthlab://manual/nutrition/2026-04-09/lunch",
                confidence_score=0.99,
            )

            wrong_day_result = append_fragment_and_regenerate_daily_context(
                bundle_path=str(bundle_path),
                output_dir=str(health_dir),
                fragment=wrong_day["bundle_fragment"],
                user_id="user_1",
                date="2026-04-09",
            )
            invalid_result = append_fragment_and_regenerate_daily_context(
                bundle_path=str(bundle_path),
                output_dir=str(health_dir),
                fragment=invalid["bundle_fragment"],
                user_id="user_1",
                date="2026-04-09",
            )

            self.assertFalse(wrong_day_result["ok"])
            self.assertEqual(wrong_day_result["error"]["code"], "bundle_fragment_scope_mismatch")
            self.assertIn(
                "date_mismatch",
                {issue["code"] for issue in wrong_day_result["validation"]["semantic_issues"]},
            )
            self.assertFalse(invalid_result["ok"])
            self.assertEqual(invalid_result["error"]["code"], "invalid_bundle_fragment")
            self.assertIn(
                "invalid_manual_payload_shape",
                {issue["code"] for issue in invalid_result["validation"]["semantic_issues"]},
            )

            self.assertEqual(bundle_path.read_text(), original_bundle_text)
            self.assertFalse((health_dir / "agent_readable_daily_context_2026-04-09.json").exists())
            self.assertFalse((health_dir / "agent_readable_daily_context_latest.json").exists())

    def test_atomic_entrypoint_rolls_back_bundle_and_artifact_outputs_when_regenerate_write_fails(self) -> None:
        base_bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        deterministic_ids = iter(
            [
                "artifact_hydration_20260409",
                "manual_hydration_20260409",
                "event_hydration_20260409",
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "health_model.agent_interface._new_id", side_effect=lambda prefix: next(deterministic_ids)
        ):
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            write_persisted_bundle(bundle_path=str(bundle_path), bundle=base_bundle)
            original_bundle_text = bundle_path.read_text()

            dated_path = health_dir / "agent_readable_daily_context_2026-04-09.json"
            latest_path = health_dir / "agent_readable_daily_context_latest.json"
            dated_path.parent.mkdir(parents=True, exist_ok=True)
            dated_path.write_text('{"state": "prior-dated"}\n')
            latest_path.write_text('{"state": "prior-latest"}\n')
            original_dated_text = dated_path.read_text()
            original_latest_text = latest_path.read_text()

            hydration = submit_hydration_log(
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

            original_replace = daily_context_artifact_module._replace_artifact_file
            call_count = 0

            def fail_after_first_replace(*, source_path: Path, target_path: Path) -> None:
                nonlocal call_count
                call_count += 1
                original_replace(source_path=source_path, target_path=target_path)
                if call_count == 1:
                    raise RuntimeError("simulated mid-write failure")

            with patch.object(
                daily_context_artifact_module,
                "_replace_artifact_file",
                side_effect=fail_after_first_replace,
            ):
                with self.assertRaisesRegex(RuntimeError, "simulated mid-write failure"):
                    append_fragment_and_regenerate_daily_context(
                        bundle_path=str(bundle_path),
                        output_dir=str(health_dir),
                        fragment=hydration["bundle_fragment"],
                        user_id="user_1",
                        date="2026-04-09",
                    )

            self.assertEqual(bundle_path.read_text(), original_bundle_text)
            self.assertEqual(dated_path.read_text(), original_dated_text)
            self.assertEqual(latest_path.read_text(), original_latest_text)
            self.assertNotIn("manual_hydration_20260409", bundle_path.read_text())
            self.assertNotIn("artifact_hydration_20260409", dated_path.read_text())
            self.assertNotIn("artifact_hydration_20260409", latest_path.read_text())

        
    def test_atomic_entrypoint_rejects_non_nutrition_hydration_fragments_without_mutation(self) -> None:
        base_bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        deterministic_ids = iter(["artifact_gym_20260409", "manual_gym_20260409"])

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "health_model.agent_interface._new_id", side_effect=lambda prefix: next(deterministic_ids)
        ):
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            write_persisted_bundle(bundle_path=str(bundle_path), bundle=base_bundle)
            original_bundle_text = bundle_path.read_text()

            gym_set = submit_gym_set(
                user_id="user_1",
                date="2026-04-09",
                exercise_name="Back squat",
                set_index=1,
                reps=5,
                weight_kg=100,
                completeness_state="complete",
                collected_at="2026-04-09T09:00:00+01:00",
                ingested_at="2026-04-09T09:00:03+01:00",
                raw_location="healthlab://manual/gym/2026-04-09/session-1",
                confidence_score=0.97,
            )

            result = append_fragment_and_regenerate_daily_context(
                bundle_path=str(bundle_path),
                output_dir=str(health_dir),
                fragment=gym_set["bundle_fragment"],
                user_id="user_1",
                date="2026-04-09",
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "unsupported_bundle_fragment")
            self.assertIn(
                "unsupported_manual_log_type",
                {issue["code"] for issue in result["validation"]["semantic_issues"]},
            )
            self.assertEqual(bundle_path.read_text(), original_bundle_text)


if __name__ == "__main__":
    unittest.main()
