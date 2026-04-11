from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RECOMMENDATION_FIXTURE = REPO_ROOT / "data" / "health" / "agent_recommendation_2026-04-10.json"


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
