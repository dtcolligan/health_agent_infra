from __future__ import annotations

import unittest

from health_model.semantic_summaries import (
    SLEEP_DISRUPTION_MARKERS,
    build_activity_training_semantic_summary,
    build_sleep_semantic_summary,
    build_subjective_state_semantic_summary,
)


class SemanticSummariesTest(unittest.TestCase):
    def test_confidence_thresholds_follow_frozen_contract(self) -> None:
        bundle = {
            "input_events": [
                _event("event_sleep_start", "sleep", "sleep_start", "string", "2026-04-08T22:45:00+01:00", confidence_score=0.8),
                _event("event_sleep_end", "sleep", "sleep_end", "string", "2026-04-09T06:55:00+01:00", confidence_score=0.5),
                _event("event_sleep_duration", "sleep", "sleep_duration_minutes", "number", 490.0, confidence_score=0.49),
            ],
            "subjective_daily_entries": [],
        }

        summary = build_sleep_semantic_summary(bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(summary.primary_sleep_window.confidence_label, "medium")
        self.assertEqual(summary.primary_sleep_window.confidence_score, 0.5)
        self.assertEqual(summary.total_sleep_duration_minutes.confidence_label, "low")

    def test_build_sleep_summary_preserves_grounded_disruption_markers(self) -> None:
        bundle = {
            "input_events": [
                _event("event_sleep_start", "sleep", "sleep_start", "string", "2026-04-08T22:45:00+01:00"),
                _event("event_sleep_end", "sleep", "sleep_end", "string", "2026-04-09T06:55:00+01:00"),
                _event("event_sleep_duration", "sleep", "sleep_duration_minutes", "number", 490.0),
                _event("event_awake_count", "sleep", "awake_count", "number", 4),
                _event("event_awake_minutes", "sleep", "awake_duration_minutes", "number", 34),
                _event("event_restless", "sleep", "restless_moments", "number", 2),
                _event("event_timing", "sleep", "sleep_timing_regularity_marker", "enum", "slightly_irregular"),
            ],
            "subjective_daily_entries": [
                _subjective_entry("subjective_sleep", perceived_sleep_quality=2),
            ],
        }

        summary = build_sleep_semantic_summary(bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(summary.primary_sleep_window.status, "grounded")
        self.assertEqual(summary.total_sleep_duration_minutes.value, 490.0)
        self.assertEqual(summary.subjective_sleep_quality.value, 2)
        self.assertEqual(summary.sleep_timing_regularity_marker.value, "slightly_irregular")
        self.assertEqual(
            set(summary.sleep_disruption_markers.value),
            {"frequent_awakenings", "prolonged_awake_time", "restless_sleep"},
        )
        self.assertTrue(set(summary.sleep_disruption_markers.value).issubset(SLEEP_DISRUPTION_MARKERS))

    def test_build_subjective_summary_keeps_perceived_recovery_grounded_inferred_and_missing_distinct(self) -> None:
        grounded_bundle = {
            "input_events": [
                _event(
                    "event_recovery",
                    "subjective",
                    "perceived_recovery_state",
                    "enum",
                    "recovered",
                    confidence_score=0.82,
                )
            ],
            "subjective_daily_entries": [_subjective_entry("subjective_grounded", perceived_sleep_quality=4)],
        }
        grounded = build_subjective_state_semantic_summary(grounded_bundle, user_id="user_1", date="2026-04-09")
        self.assertEqual(grounded.perceived_recovery.status, "grounded")
        self.assertEqual(grounded.perceived_recovery.value, "recovered")

        inferred_bundle = {
            "input_events": [],
            "subjective_daily_entries": [_subjective_entry("subjective_inferred", perceived_sleep_quality=2)],
        }
        inferred = build_subjective_state_semantic_summary(inferred_bundle, user_id="user_1", date="2026-04-09")
        self.assertEqual(inferred.perceived_recovery.status, "inferred")
        self.assertEqual(inferred.perceived_recovery.value, "strained")

        missing_bundle = {"input_events": [], "subjective_daily_entries": []}
        missing = build_subjective_state_semantic_summary(missing_bundle, user_id="user_1", date="2026-04-09")
        self.assertEqual(missing.perceived_recovery.status, "missing")
        self.assertIn("missing_recovery_signal", {gap.code for gap in missing.important_gaps})

    def test_build_subjective_summary_surfaces_top_level_recovery_conflicts(self) -> None:
        bundle = {
            "input_events": [
                _event("event_recovery_1", "subjective", "perceived_recovery_state", "enum", "recovered", confidence_score=0.84),
                _event("event_recovery_2", "subjective", "perceived_recovery_state", "enum", "strained", confidence_score=0.84),
            ],
            "subjective_daily_entries": [_subjective_entry("subjective_conflicted", perceived_sleep_quality=3)],
        }

        summary = build_subjective_state_semantic_summary(bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(summary.perceived_recovery.status, "conflicted")
        self.assertIn("conflicting_perceived_recovery", {conflict.code for conflict in summary.conflicts})

    def test_build_activity_training_summary_separates_passive_activity_from_intentional_training(self) -> None:
        bundle = {
            "input_events": [
                _event("event_steps", "running", "steps_count", "number", 10234),
                _event("event_active_minutes", "running", "active_minutes", "number", 71),
                _event("event_active_energy", "running", "active_energy_kcal", "number", 612),
                _event("event_run_duration", "running", "run_duration_minutes", "number", 42, source_record_id="run_1"),
            ],
            "subjective_daily_entries": [
                _subjective_entry("subjective_training", illness_or_soreness_flag=True),
            ],
            "manual_log_entries": [
                _manual_entry("manual_gym_session", "gym_session", {"session_label": "Upper"}),
                _manual_entry("manual_set_1", "exercise_set", {"exercise_name": "Bench Press", "set_index": 1}),
                _manual_entry("manual_body_signal", "body_signal", {"signal_type": "soreness", "severity": 2}),
            ],
        }

        summary = build_activity_training_semantic_summary(bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(summary.passive_activity.steps_count.status, "grounded")
        self.assertEqual(summary.passive_activity.steps_count.value, 10234.0)
        self.assertEqual(summary.intentional_training.run_session_count.value, 1)
        self.assertEqual(summary.intentional_training.gym_session_count.value, 1)
        self.assertEqual(summary.intentional_training.gym_exercise_set_count.value, 1)
        self.assertEqual(summary.training_load_estimate_band.status, "inferred")
        self.assertEqual(summary.training_load_estimate_band.value, "moderate")
        self.assertEqual(
            set(summary.training_completion_markers.value),
            {"run_completed", "gym_session_logged"},
        )
        self.assertEqual(
            set(summary.soreness_or_strain_context.value),
            {"manual_body_signal_logged", "reported_soreness_or_illness"},
        )

    def test_build_activity_training_summary_surfaces_top_level_passive_activity_conflicts(self) -> None:
        bundle = {
            "input_events": [
                _event("event_steps_1", "running", "steps_count", "number", 9000),
                _event("event_steps_2", "running", "steps_count", "number", 11000),
            ],
            "subjective_daily_entries": [],
            "manual_log_entries": [],
        }

        summary = build_activity_training_semantic_summary(bundle, user_id="user_1", date="2026-04-09")

        self.assertEqual(summary.passive_activity.steps_count.status, "conflicted")
        self.assertIn("conflicting_passive_activity", {conflict.code for conflict in summary.conflicts})


def _event(
    event_id: str,
    domain: str,
    metric_name: str,
    value_type: str,
    value: object,
    *,
    confidence_score: float = 0.95,
    source_record_id: str | None = None,
) -> dict[str, object]:
    payload = {
        "event_id": event_id,
        "user_id": "user_1",
        "source_type": "wearable" if domain != "subjective" else "voice_note",
        "source_name": "test_source",
        "source_record_id": source_record_id,
        "capture_mode": "passive" if domain != "subjective" else "derived",
        "domain": domain,
        "metric_name": metric_name,
        "value_type": value_type,
        "value_number": None,
        "value_string": None,
        "value_boolean": None,
        "value_json": None,
        "event_start_at": None,
        "event_end_at": None,
        "effective_date": "2026-04-09",
        "ingested_at": "2026-04-10T08:00:00Z",
        "confidence_label": "high" if confidence_score >= 0.8 else "medium" if confidence_score >= 0.5 else "low",
        "confidence_score": confidence_score,
        "missingness_state": "present",
        "provenance": {
            "artifact_id": "artifact_test",
            "derivation_method": "wearable_normalization" if domain != "subjective" else "voice_extraction",
            "supporting_refs": [],
            "conflict_status": "none",
        },
    }
    if value_type == "number":
        payload["value_number"] = value
    else:
        payload["value_string"] = value
    return payload


def _subjective_entry(
    entry_id: str,
    *,
    perceived_sleep_quality: int | None = None,
    illness_or_soreness_flag: bool | None = None,
) -> dict[str, object]:
    return {
        "entry_id": entry_id,
        "user_id": "user_1",
        "date": "2026-04-09",
        "energy_self_rating": 3,
        "stress_self_rating": 2,
        "mood_self_rating": 4,
        "perceived_sleep_quality": perceived_sleep_quality,
        "illness_or_soreness_flag": illness_or_soreness_flag,
        "free_text_summary": "Worked example subjective summary.",
        "extraction_status": "complete",
        "source_artifact_ids": ["artifact_voice"],
        "confidence_label": "medium",
        "confidence_score": 0.76,
    }


def _manual_entry(entry_id: str, log_type: str, payload: dict[str, object]) -> dict[str, object]:
    return {
        "entry_id": entry_id,
        "user_id": "user_1",
        "date": "2026-04-09",
        "log_type": log_type,
        "payload": payload,
        "source_artifact_id": "artifact_manual",
        "completeness_state": "complete",
        "confidence_label": "high",
        "confidence_score": 0.98,
    }


if __name__ == "__main__":
    unittest.main()
