from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RECOMMENDATION_FIXTURE = REPO_ROOT / "data" / "health" / "agent_recommendation_2026-04-10.json"
TRANSITION_FIXTURE_ROOT = REPO_ROOT / "artifacts" / "protocol_layer_proof" / "2026-04-11-recommendation-resolution-window-selective-transition"


class AgentMemoryWriteCliIntegrationTest(unittest.TestCase):
    def test_recommendation_judgment_writes_dated_and_latest_artifacts_for_valid_payload(self) -> None:
        recommendation = json.loads(RECOMMENDATION_FIXTURE.read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            payload = {
                "user_id": "user_dom",
                "date": "2026-04-10",
                "recommendation_artifact_path": str(RECOMMENDATION_FIXTURE),
                "recommendation_artifact_id": recommendation["recommendation_id"],
                "judgment_id": "judgment_20260410_01",
                "judgment_label": "useful",
                "action_taken": "Kept the evening light and skipped extra load.",
                "why": "The recommendation matched the low-energy and soreness signals and was easy to act on.",
                "written_at": "2026-04-10T20:15:00+01:00",
                "request_id": "req_judgment_01",
                "requested_at": "2026-04-10T20:14:00+01:00",
                "caveat": "No sleep-duration evidence was available.",
                "time_cost_note": "About 5 minutes.",
                "friction_points": ["manual payload review"],
            }

            result = self._run_cli(["recommendation-judgment", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)])

            self.assertTrue(result["ok"], msg=result)
            self.assertIsNone(result["error"])
            self.assertTrue(result["validation"]["is_valid"])
            self.assertEqual(result["writeback"]["artifact_type"], "recommendation_judgment")
            self.assertEqual(result["writeback"]["recommendation_artifact_id"], recommendation["recommendation_id"])
            self.assertEqual(result["writeback"]["recommendation_evidence_refs"], recommendation["evidence_refs"])

            dated_path = Path(result["artifact_path"])
            latest_path = Path(result["latest_artifact_path"])
            self.assertTrue(dated_path.exists())
            self.assertTrue(latest_path.exists())
            self.assertEqual(dated_path.read_bytes(), latest_path.read_bytes())
            self.assertEqual(json.loads(dated_path.read_text()), result["writeback"])

    def test_recommendation_judgment_rejects_wrong_scope(self) -> None:
        recommendation = json.loads(RECOMMENDATION_FIXTURE.read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            payload = {
                "user_id": "wrong_user",
                "date": "2026-04-10",
                "recommendation_artifact_path": str(RECOMMENDATION_FIXTURE),
                "recommendation_artifact_id": recommendation["recommendation_id"],
                "judgment_id": "judgment_bad_scope",
                "judgment_label": "useful",
                "action_taken": "Action",
                "why": "Why",
                "written_at": "2026-04-10T20:15:00+01:00",
                "request_id": "req_bad_scope",
                "requested_at": "2026-04-10T20:14:00+01:00",
            }

            result = self._run_cli(
                ["recommendation-judgment", "--output-dir", str(Path(temp_dir) / "data" / "health"), "--payload-json", json.dumps(payload)],
                expected_returncode=1,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "artifact_user_mismatch")
            self.assertTrue(any(issue["code"] == "artifact_user_mismatch" for issue in result["validation"]["semantic_issues"]))

    def test_recommendation_judgment_rejects_missing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing_recommendation.json"
            payload = {
                "user_id": "user_dom",
                "date": "2026-04-10",
                "recommendation_artifact_path": str(missing_path),
                "recommendation_artifact_id": "rec_missing_01",
                "judgment_id": "judgment_missing_artifact",
                "judgment_label": "useful",
                "action_taken": "Action",
                "why": "Why",
                "written_at": "2026-04-10T20:15:00+01:00",
                "request_id": "req_missing_artifact",
                "requested_at": "2026-04-10T20:14:00+01:00",
            }

            result = self._run_cli(
                ["recommendation-judgment", "--output-dir", str(Path(temp_dir) / "data" / "health"), "--payload-json", json.dumps(payload)],
                expected_returncode=1,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "recommendation_artifact_not_found")
            self.assertTrue(any(issue["code"] == "recommendation_artifact_not_found" for issue in result["validation"]["semantic_issues"]))

    def test_recommendation_judgment_rejects_mismatched_recommendation_id_without_mutation(self) -> None:
        recommendation = json.loads(RECOMMENDATION_FIXTURE.read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            health_dir.mkdir(parents=True, exist_ok=True)
            dated_path = health_dir / "recommendation_judgment_2026-04-10.json"
            latest_path = health_dir / "recommendation_judgment_latest.json"
            original_bytes = (
                json.dumps(
                    {
                        "artifact_type": "recommendation_judgment",
                        "user_id": "user_dom",
                        "date": "2026-04-10",
                        "judgment_id": "judgment_existing_01",
                        "judgment_label": "obvious",
                        "action_taken": "Existing action.",
                        "why": "Existing why.",
                        "written_at": "2026-04-10T19:00:00+01:00",
                        "request_id": "req_existing",
                        "requested_at": "2026-04-10T18:59:00+01:00",
                        "recommendation_artifact_path": str(RECOMMENDATION_FIXTURE),
                        "recommendation_artifact_id": recommendation["recommendation_id"],
                        "recommendation_evidence_refs": recommendation["evidence_refs"],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode()
            dated_path.write_bytes(original_bytes)
            latest_path.write_bytes(original_bytes)

            payload = {
                "user_id": "user_dom",
                "date": "2026-04-10",
                "recommendation_artifact_path": str(RECOMMENDATION_FIXTURE),
                "recommendation_artifact_id": "wrong_recommendation_id",
                "judgment_id": "judgment_rejected_01",
                "judgment_label": "useful",
                "action_taken": "Action",
                "why": "Why",
                "written_at": "2026-04-10T20:15:00+01:00",
                "request_id": "req_rejected_01",
                "requested_at": "2026-04-10T20:14:00+01:00",
            }

            result = self._run_cli(
                ["recommendation-judgment", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)],
                expected_returncode=1,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "recommendation_artifact_id_mismatch")
            self.assertEqual(dated_path.read_bytes(), original_bytes)
            self.assertEqual(latest_path.read_bytes(), original_bytes)

    def test_recommendation_resolution_transition_writes_updated_resolution_and_feedback_locators(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "out"
            payload = {
                "user_id": "user_dom",
                "start_date": "2026-04-04",
                "end_date": "2026-04-10",
                "recommendation_artifact_path": str(TRANSITION_FIXTURE_ROOT / "agent_recommendation_2026-04-07.json"),
                "recommendation_artifact_id": "rec_window_20260407_walk_01",
                "judgment_artifact_path": str(TRANSITION_FIXTURE_ROOT / "recommendation_judgment_2026-04-07.json"),
                "judgment_artifact_id": "judgment_window_selective_transition_20260407_01",
                "resolution_window_memory_path": str(TRANSITION_FIXTURE_ROOT / "recommendation_resolution_window_before_memory.json"),
                "feedback_window_memory_path": str(TRANSITION_FIXTURE_ROOT / "recommendation_feedback_window_after_memory.json"),
                "written_at": "2026-04-11T14:31:00+01:00",
                "request_id": "req_transition_test_success",
                "requested_at": "2026-04-11T14:30:00+01:00",
            }

            result = self._run_cli([
                "recommendation-resolution-transition",
                "--output-dir", str(output_dir),
                "--payload-json", json.dumps(payload),
            ])

            self.assertTrue(result["ok"], msg=result)
            resolution_path = Path(result["artifact_path"])
            resolution_latest = Path(result["latest_artifact_path"])
            self.assertTrue(resolution_path.exists())
            self.assertEqual(resolution_path.read_bytes(), resolution_latest.read_bytes())
            locator = json.loads(resolution_path.read_text())
            target_entry = next(entry for entry in locator["accepted_recommendations"] if entry["date"] == "2026-04-07")
            self.assertEqual(Path(target_entry["judgment_artifact_path"]).resolve(), (TRANSITION_FIXTURE_ROOT / "recommendation_judgment_2026-04-07.json").resolve())
            self.assertFalse(any(entry.get("date") == "2026-04-04" and entry.get("judgment_artifact_path") is None for entry in locator["accepted_recommendations"]))

            feedback_written = result["writeback"]["written_locator_artifacts"]["feedback_window"]
            self.assertIsNotNone(feedback_written)
            feedback_locator = json.loads(Path(feedback_written["artifact_path"]).read_text())
            self.assertEqual(len(feedback_locator["accepted_feedback_pairs"]), 3)
            self.assertTrue(any(entry["date"] == "2026-04-07" for entry in feedback_locator["accepted_feedback_pairs"]))

    def test_recommendation_resolution_transition_rejects_duplicate_target_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            locator_path = Path(temp_dir) / "recommendation_resolution_window_memory.json"
            locator_payload = json.loads((TRANSITION_FIXTURE_ROOT / "recommendation_resolution_window_before_memory.json").read_text())
            locator_payload["accepted_recommendations"].append(dict(locator_payload["accepted_recommendations"][1]))
            locator_path.write_text(json.dumps(locator_payload, indent=2, sort_keys=True) + "\n")

            output_dir = Path(temp_dir) / "out"
            output_dir.mkdir(parents=True, exist_ok=True)
            existing_dated = output_dir / "recommendation_resolution_window_memory_2026-04-04_2026-04-10.json"
            existing_latest = output_dir / "recommendation_resolution_window_memory_latest.json"
            original = b'{"keep":"original"}\n'
            existing_dated.write_bytes(original)
            existing_latest.write_bytes(original)

            payload = {
                "user_id": "user_dom",
                "start_date": "2026-04-04",
                "end_date": "2026-04-10",
                "recommendation_artifact_path": str(TRANSITION_FIXTURE_ROOT / "agent_recommendation_2026-04-07.json"),
                "recommendation_artifact_id": "rec_window_20260407_walk_01",
                "judgment_artifact_path": str(TRANSITION_FIXTURE_ROOT / "recommendation_judgment_2026-04-07.json"),
                "judgment_artifact_id": "judgment_window_selective_transition_20260407_01",
                "resolution_window_memory_path": str(locator_path),
                "written_at": "2026-04-11T14:31:00+01:00",
                "request_id": "req_transition_test_reject",
                "requested_at": "2026-04-11T14:30:00+01:00",
            }

            result = self._run_cli([
                "recommendation-resolution-transition",
                "--output-dir", str(output_dir),
                "--payload-json", json.dumps(payload),
            ], expected_returncode=1)

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "duplicate_recommendation_entry")
            self.assertEqual(existing_dated.read_bytes(), original)
            self.assertEqual(existing_latest.read_bytes(), original)

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_memory_write_cli", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected_returncode, msg=completed.stderr or completed.stdout)
        self.assertEqual(completed.stderr.strip(), "")
        self.assertTrue(completed.stdout.strip())
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
