from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from health_model.daily_snapshot import (
    build_gym_sessions,
    build_manual_resistance_training_bundle,
    build_manual_resistance_training_objects,
    generate_snapshot,
    write_manual_resistance_training_proof_artifacts,
)
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

    def test_manual_gym_sessions_emit_frozen_ids_and_totals(self) -> None:
        sessions_payload = [
            {
                "session_key": "example-upper-2026-04-08",
                "date": "2026-04-08",
                "sets": [
                    {"set_key": "bench-1", "exercise_name": "Bench press", "set_number": 1, "reps": 8, "weight_kg": 60},
                    {"set_key": "bench-2", "exercise_name": "Bench press", "set_number": 2, "reps": 8, "weight_kg": 60},
                    {"set_key": "pulldown-1", "exercise_name": "Lat pulldown", "set_number": 1, "reps": 10, "weight_kg": 45},
                ],
            }
        ]

        sessions, sets = build_gym_sessions(sessions_payload, "2026-04-08", source_artifact="manual_gym_sessions")

        self.assertEqual(len(sessions), 1)
        self.assertEqual(len(sets), 3)
        self.assertEqual(sessions[0].training_session_id, "resistance_training:manual_gym_sessions:session:example-upper-2026-04-08")
        self.assertEqual(sessions[0].source_record_id, sessions[0].training_session_id)
        self.assertEqual(sessions[0].provenance_record_id, "provenance:resistance_training:manual_gym_sessions:training_session:example-upper-2026-04-08")
        self.assertEqual(sessions[0].confidence_label, "high")
        self.assertEqual(sessions[0].conflict_status, "none")
        self.assertEqual(sessions[0].exercise_count, 2)
        self.assertEqual(sessions[0].total_sets, 3)
        self.assertEqual(sessions[0].total_reps, 26)
        self.assertEqual(sessions[0].total_load_kg, 1410.0)
        self.assertEqual(sets[0].gym_exercise_set_id, "resistance_training:manual_gym_sessions:set:example-upper-2026-04-08:bench-1")
        self.assertEqual(sets[0].training_session_id, sessions[0].training_session_id)
        self.assertEqual(sets[0].source_name, "resistance_training")
        self.assertEqual(sets[0].source_record_id, sets[0].gym_exercise_set_id)
        self.assertEqual(sets[0].provenance_record_id, "provenance:resistance_training:manual_gym_sessions:gym_exercise_set:example-upper-2026-04-08:bench-1")
        self.assertEqual(sets[0].confidence_label, "high")
        self.assertEqual(sets[0].conflict_status, "none")
        self.assertEqual(sets[0].compatibility_status, "legacy_compatibility_only")
        self.assertEqual(sets[0].canonical_artifact_family, "gym_set_record")

        replay_sessions, replay_sets = build_gym_sessions(sessions_payload, "2026-04-08", source_artifact="manual_gym_sessions")
        self.assertEqual([row.training_session_id for row in sessions], [row.training_session_id for row in replay_sessions])
        self.assertEqual([row.gym_exercise_set_id for row in sets], [row.gym_exercise_set_id for row in replay_sets])

    def test_manual_resistance_training_objects_emit_contract_named_rows(self) -> None:
        sessions_payload = [
            {
                "session_key": "example-upper-2026-04-08",
                "date": "2026-04-08",
                "sets": [
                    {"set_key": "bench-1", "exercise_name": "Bench press", "exercise_group": "chest", "set_number": 1, "reps": 8, "weight_kg": 60},
                    {"set_key": "bench-2", "exercise_name": "Bench press", "exercise_group": "chest", "set_number": 2, "reps": 8, "weight_kg": 60},
                    {"set_key": "pulldown-1", "exercise_name": "Lat pulldown", "exercise_group": "back", "set_number": 1, "reps": 10, "weight_kg": 45},
                ],
            }
        ]

        sessions, exercise_catalog, exercise_alias, gym_set_records = build_manual_resistance_training_objects(
            sessions_payload,
            "2026-04-08",
            source_artifact="manual_gym_sessions",
        )

        self.assertEqual([row.training_session_id for row in sessions], ["resistance_training:manual_gym_sessions:session:example-upper-2026-04-08"])
        self.assertEqual(
            [row.exercise_catalog_id for row in exercise_catalog],
            [
                "exercise_catalog:resistance_training:manual_gym_sessions:exercise:bench-press",
                "exercise_catalog:resistance_training:manual_gym_sessions:exercise:lat-pulldown",
            ],
        )
        self.assertEqual([row.alias_name for row in exercise_alias], ["Bench press", "Lat pulldown"])
        self.assertEqual(
            [row.exercise_alias_id for row in exercise_alias],
            [
                "exercise_alias:resistance_training:manual_gym_sessions:exercise:bench-press:alias:bench-press",
                "exercise_alias:resistance_training:manual_gym_sessions:exercise:lat-pulldown:alias:lat-pulldown",
            ],
        )
        self.assertEqual(
            [row.gym_set_record_id for row in gym_set_records],
            [
                "gym_set_record:resistance_training:manual_gym_sessions:set:example-upper-2026-04-08:bench-1",
                "gym_set_record:resistance_training:manual_gym_sessions:set:example-upper-2026-04-08:bench-2",
                "gym_set_record:resistance_training:manual_gym_sessions:set:example-upper-2026-04-08:pulldown-1",
            ],
        )
        self.assertTrue(all(row.training_session_id == sessions[0].training_session_id for row in gym_set_records))
        self.assertEqual(gym_set_records[0].source_record_id, "resistance_training:manual_gym_sessions:set:example-upper-2026-04-08:bench-1")
        self.assertEqual(gym_set_records[0].exercise_catalog_id, exercise_catalog[0].exercise_catalog_id)
        self.assertEqual(gym_set_records[0].exercise_alias_id, exercise_alias[0].exercise_alias_id)

    def test_manual_resistance_training_bundle_proves_replay_stability_and_defers_program_block(self) -> None:
        export_dir = FIXTURES_DIR / "garmin_minimal_export"
        gym_log_path = Path("merge_human_inputs/examples/manual_gym_sessions.example.json")
        bundle = build_manual_resistance_training_bundle(export_dir, gym_log_path, "2026-04-08")

        self.assertEqual([row["training_session_id"] for row in bundle["training_sessions"]], ["resistance_training:manual_gym_sessions.example:session:upper-2026-04-08"])
        self.assertEqual(
            [row["exercise_catalog_id"] for row in bundle["exercise_catalog"]],
            [
                "exercise_catalog:resistance_training:manual_gym_sessions.example:exercise:bench-press",
                "exercise_catalog:resistance_training:manual_gym_sessions.example:exercise:lat-pulldown",
            ],
        )
        self.assertEqual(
            [row["exercise_alias_id"] for row in bundle["exercise_alias"]],
            [
                "exercise_alias:resistance_training:manual_gym_sessions.example:exercise:bench-press:alias:bench-press",
                "exercise_alias:resistance_training:manual_gym_sessions.example:exercise:lat-pulldown:alias:lat-pulldown",
            ],
        )
        self.assertEqual(
            [row["gym_set_record_id"] for row in bundle["gym_set_record"]],
            [
                "gym_set_record:resistance_training:manual_gym_sessions.example:set:upper-2026-04-08:bench-press-1",
                "gym_set_record:resistance_training:manual_gym_sessions.example:set:upper-2026-04-08:lat-pulldown-1",
            ],
        )
        self.assertEqual(bundle["daily_health_snapshot"]["gym_sessions_count"], 1)
        self.assertEqual(bundle["daily_health_snapshot"]["gym_total_sets"], 2)
        self.assertEqual(bundle["daily_health_snapshot"]["gym_total_reps"], 18)
        self.assertEqual(bundle["daily_health_snapshot"]["gym_total_load_kg"], 930.0)
        self.assertEqual(
            [row["gym_set_record_id"] for row in bundle["daily_health_snapshot"]["gym_set_records"]],
            [
                "gym_set_record:resistance_training:manual_gym_sessions.example:set:upper-2026-04-08:bench-press-1",
                "gym_set_record:resistance_training:manual_gym_sessions.example:set:upper-2026-04-08:lat-pulldown-1",
            ],
        )
        self.assertEqual(bundle["daily_health_snapshot"]["legacy_compatibility_aliases"], {"gym_exercise_sets": "gym_set_records"})
        self.assertTrue(all(row["compatibility_status"] == "legacy_compatibility_only" for row in bundle["daily_health_snapshot"]["gym_exercise_sets"]))

        with tempfile.TemporaryDirectory() as tmpdir:
            proof = write_manual_resistance_training_proof_artifacts(export_dir, gym_log_path, Path(tmpdir), "2026-04-08")
            manifest = json.loads(Path(proof["proof_manifest"]).read_text())
            stable = json.loads((Path(tmpdir) / "stable_id_evidence.json").read_text())

        self.assertIn("exercise_catalog", manifest["checked_in_artifacts"])
        self.assertIn("exercise_alias", manifest["checked_in_artifacts"])
        self.assertIn("gym_set_record", manifest["checked_in_artifacts"])
        self.assertIn("program_block remains explicitly deferred", " ".join(manifest["limits"]))
        self.assertTrue(stable["replays_match"]["training_session_ids"])
        self.assertTrue(stable["replays_match"]["exercise_catalog_ids"])
        self.assertTrue(stable["replays_match"]["exercise_alias_ids"])
        self.assertTrue(stable["replays_match"]["gym_set_record_ids"])
        self.assertTrue(stable["replays_match"]["daily_rollups"]["gym_total_load_kg"])

    def test_generate_snapshot_rolls_manual_gym_metrics_consistently(self) -> None:
        export_dir = FIXTURES_DIR / "garmin_minimal_export"
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "health_log.db"
            gym_log_path = Path(tmpdir) / "manual_gym_sessions.json"
            gym_log_path.write_text(json.dumps({
                "schema_version": 1,
                "sessions": [
                    {
                        "session_key": "example-upper-2026-04-08",
                        "date": "2026-04-08",
                        "start_time_local": "2026-04-08T18:00:00",
                        "session_title": "Upper body",
                        "lift_focus": "push_pull",
                        "duration_sec": 3000,
                        "rpe_1_10": 7,
                        "energy_pre_1_5": 3,
                        "energy_post_1_5": 2,
                        "notes": "Example manual gym log for Health Lab v1.",
                        "sets": [
                            {"set_key": "bench-1", "exercise_name": "Bench press", "exercise_group": "chest", "set_number": 1, "reps": 8, "weight_kg": 60},
                            {"set_key": "bench-2", "exercise_name": "Bench press", "exercise_group": "chest", "set_number": 2, "reps": 8, "weight_kg": 60},
                            {"set_key": "pulldown-1", "exercise_name": "Lat pulldown", "exercise_group": "back", "set_number": 1, "reps": 10, "weight_kg": 45}
                        ]
                    }
                ]
            }))
            snapshot = generate_snapshot(export_dir=export_dir, gym_log_path=gym_log_path, db_path=db_path, target_date="2026-04-08", user_id=1)
            replay = generate_snapshot(export_dir=export_dir, gym_log_path=gym_log_path, db_path=db_path, target_date="2026-04-08", user_id=1)

        self.assertEqual(snapshot.gym_sessions_count, 1)
        self.assertEqual(snapshot.gym_total_sets, 3)
        self.assertEqual(snapshot.gym_total_reps, 26)
        self.assertEqual(snapshot.gym_total_load_kg, 1410.0)
        self.assertEqual(snapshot.gym_sessions[0]["training_session_id"], "resistance_training:manual_gym_sessions:session:example-upper-2026-04-08")
        self.assertEqual(snapshot.gym_set_records[0]["gym_set_record_id"], "gym_set_record:resistance_training:manual_gym_sessions:set:example-upper-2026-04-08:bench-1")
        self.assertEqual(snapshot.gym_exercise_sets[0]["gym_exercise_set_id"], "resistance_training:manual_gym_sessions:set:example-upper-2026-04-08:bench-1")
        self.assertEqual(snapshot.gym_exercise_sets[0]["compatibility_status"], "legacy_compatibility_only")
        self.assertEqual(snapshot.legacy_compatibility_aliases, {"gym_exercise_sets": "gym_set_records"})
        self.assertEqual(snapshot.gym_sessions, replay.gym_sessions)
        self.assertEqual(snapshot.gym_set_records, replay.gym_set_records)
        self.assertEqual(snapshot.gym_exercise_sets, replay.gym_exercise_sets)
        self.assertIn("gym_total_load_kg", snapshot.data_backed_fields)


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_DIR / name).read_text())


if __name__ == "__main__":
    unittest.main()
