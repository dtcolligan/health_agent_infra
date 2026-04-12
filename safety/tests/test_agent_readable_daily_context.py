from __future__ import annotations

import json
import unittest
from pathlib import Path

from health_model import build_agent_readable_daily_context, validate_shared_input_bundle


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readable_daily_context"


class AgentReadableDailyContextTest(unittest.TestCase):
    def test_fixture_day_bundle_emits_expected_agent_context(self) -> None:
        bundle = json.loads((FIXTURE_DIR / "fixture_day_bundle.json").read_text())
        expected = json.loads((FIXTURE_DIR / "generated_fixture_day_context.json").read_text())

        validation = validate_shared_input_bundle(bundle)

        self.assertTrue(validation.is_valid, msg=f"schema={validation.schema_issues} semantic={validation.semantic_issues}")

        artifact = build_agent_readable_daily_context(bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(artifact, expected)
        self.assertEqual(artifact["artifact_type"], "agent_readable_daily_context")
        self.assertGreater(artifact["explicit_grounding"]["signal_status_counts"]["grounded"], 0)
        self.assertGreater(artifact["explicit_grounding"]["signal_status_counts"]["inferred"], 0)
        self.assertGreater(artifact["explicit_grounding"]["signal_status_counts"]["missing"], 0)
        self.assertGreater(artifact["explicit_grounding"]["signal_status_counts"]["conflicted"], 0)
        self.assertIn("missing_subjective_sleep_quality", {gap["code"] for gap in artifact["important_gaps"]})
        self.assertIn("conflicting_passive_activity", {conflict["code"] for conflict in artifact["conflicts"]})

    def test_multi_day_bundle_scopes_provenance_to_selected_day(self) -> None:
        bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        validation = validate_shared_input_bundle(bundle)

        self.assertTrue(validation.is_valid, msg=f"schema={validation.schema_issues} semantic={validation.semantic_issues}")

        artifact = build_agent_readable_daily_context(bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(
            artifact["generated_from"]["source_artifact_ids"],
            [
                "artifact_manual_20260409",
                "artifact_voice_20260409",
                "artifact_wearable_20260409",
            ],
        )
        self.assertNotIn("artifact_manual_20260408", artifact["generated_from"]["source_artifact_ids"])
        self.assertNotIn("artifact_voice_20260408", artifact["generated_from"]["source_artifact_ids"])
        self.assertNotIn("artifact_wearable_20260408", artifact["generated_from"]["source_artifact_ids"])
        self.assertEqual(
            artifact["generated_from"]["input_event_ids"],
            [
                "event_active_minutes_20260409",
                "event_run_duration_20260409",
                "event_sleep_duration_20260409",
                "event_sleep_end_20260409",
                "event_sleep_start_20260409",
                "event_steps_evening_20260409",
                "event_steps_morning_20260409",
            ],
        )
        self.assertEqual(artifact["generated_from"]["subjective_entry_ids"], ["subjective_voice_20260409"])
        self.assertEqual(
            artifact["generated_from"]["manual_log_entry_ids"],
            [
                "manual_body_signal_20260409",
                "manual_gym_session_20260409",
                "manual_set_1_20260409",
            ],
        )


if __name__ == "__main__":
    unittest.main()
