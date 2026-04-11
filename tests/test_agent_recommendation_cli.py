from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTEXT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "agent_readable_daily_context" / "generated_fixture_day_context.json"
WINDOW_FIXTURE = REPO_ROOT / "artifacts" / "protocol_layer_proof" / "2026-04-11-recommendation-resolution-window" / "success_envelope.json"


class AgentRecommendationCliIntegrationTest(unittest.TestCase):
    def test_create_writes_dated_and_latest_recommendation_for_valid_scoped_context_and_resolution_window(self) -> None:
        context = json.loads(CONTEXT_FIXTURE.read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            health_dir = temp_root / "data" / "health"
            context_path = temp_root / "agent_readable_daily_context_2026-04-11.json"
            window_path = temp_root / "resolution_window_success.json"
            context_path.write_text(
                json.dumps(
                    {
                        **context,
                        "user_id": "user_dom",
                        "date": "2026-04-11",
                        "context_id": "agent_context_user_dom_2026-04-11",
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            window_path.write_text(WINDOW_FIXTURE.read_text())
            payload = self._valid_payload(context_path=context_path, window_path=window_path)

            result = self._run_cli(["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)])

            self.assertTrue(result["ok"], msg=result)
            self.assertIsNone(result["error"])
            self.assertTrue(result["validation"]["is_valid"])
            self.assertEqual(result["recommendation"]["artifact_type"], "agent_recommendation")
            self.assertEqual(result["recommendation"]["context_artifact_path"], str(context_path))
            self.assertEqual(result["recommendation"]["context_artifact_id"], payload["context_artifact_id"])
            self.assertEqual(result["recommendation"]["resolution_window_artifact_path"], str(window_path))
            self.assertEqual(result["recommendation"]["evidence_refs"], payload["evidence_refs"])
            self.assertEqual(result["recommendation"]["policy_basis"], payload["policy_basis"])

            dated_path = Path(result["artifact_path"])
            latest_path = Path(result["latest_artifact_path"])
            self.assertTrue(dated_path.exists())
            self.assertTrue(latest_path.exists())
            self.assertEqual(dated_path.read_bytes(), latest_path.read_bytes())
            self.assertEqual(json.loads(dated_path.read_text()), result["recommendation"])

    def test_create_rejects_bad_user_scope_with_fail_closed_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            health_dir = temp_root / "data" / "health"
            context_path = temp_root / "context.json"
            window_path = temp_root / "resolution_window_success.json"
            context = json.loads(CONTEXT_FIXTURE.read_text())
            context_path.write_text(json.dumps({**context, "user_id": "user_dom", "date": "2026-04-11", "context_id": "agent_context_user_dom_2026-04-11"}, indent=2, sort_keys=True) + "\n")
            window_path.write_text(WINDOW_FIXTURE.read_text())
            payload = self._valid_payload(context_path=context_path, window_path=window_path)
            payload["user_id"] = "wrong_user"

            result = self._run_cli(["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)], expected_returncode=1)

            self.assertFalse(result["ok"])
            self.assertIsNone(result["artifact_path"])
            self.assertIsNone(result["latest_artifact_path"])
            self.assertIsNone(result["recommendation"])
            self.assertEqual(result["error"]["code"], "artifact_user_mismatch")
            self.assertTrue(any(issue["code"] == "artifact_user_mismatch" for issue in result["validation"]["semantic_issues"]))

    def test_create_rejects_missing_resolution_window_artifact_with_fail_closed_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            health_dir = temp_root / "data" / "health"
            context = json.loads(CONTEXT_FIXTURE.read_text())
            context_path = temp_root / "context.json"
            context_path.write_text(json.dumps({**context, "user_id": "user_dom", "date": "2026-04-11", "context_id": "agent_context_user_dom_2026-04-11"}, indent=2, sort_keys=True) + "\n")
            missing_window_path = temp_root / "missing_window.json"
            payload = self._valid_payload(context_path=context_path, window_path=missing_window_path)

            result = self._run_cli(["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)], expected_returncode=1)

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "resolution_window_artifact_not_found")
            self.assertTrue(any(issue["code"] == "resolution_window_artifact_not_found" for issue in result["validation"]["semantic_issues"]))

    def test_create_rejects_uncited_window_reference_with_fail_closed_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            health_dir = temp_root / "data" / "health"
            context = json.loads(CONTEXT_FIXTURE.read_text())
            context_path = temp_root / "context.json"
            window_path = temp_root / "resolution_window_success.json"
            context_path.write_text(json.dumps({**context, "user_id": "user_dom", "date": "2026-04-11", "context_id": "agent_context_user_dom_2026-04-11"}, indent=2, sort_keys=True) + "\n")
            window_path.write_text(WINDOW_FIXTURE.read_text())
            payload = self._valid_payload(context_path=context_path, window_path=window_path)
            payload["policy_basis"]["prior_recommendation_refs"][0]["recommendation_id"] = "rec_missing"

            result = self._run_cli(["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)], expected_returncode=1)

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "uncited_window_reference")
            self.assertTrue(any(issue["code"] == "uncited_window_reference" for issue in result["validation"]["semantic_issues"]))

    def test_rejected_create_leaves_preexisting_recommendation_artifacts_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            health_dir = temp_root / "data" / "health"
            health_dir.mkdir(parents=True, exist_ok=True)
            context = json.loads(CONTEXT_FIXTURE.read_text())
            context_path = temp_root / "context.json"
            window_path = temp_root / "resolution_window_success.json"
            context_path.write_text(json.dumps({**context, "user_id": "user_dom", "date": "2026-04-11", "context_id": "agent_context_user_dom_2026-04-11"}, indent=2, sort_keys=True) + "\n")
            window_path.write_text(WINDOW_FIXTURE.read_text())
            dated_path = health_dir / "agent_recommendation_2026-04-11.json"
            latest_path = health_dir / "agent_recommendation_latest.json"
            original_bytes = (
                json.dumps(
                    {
                        "artifact_type": "agent_recommendation",
                        "user_id": "user_dom",
                        "date": "2026-04-11",
                        "context_artifact_path": str(context_path),
                        "context_artifact_id": "agent_context_user_dom_2026-04-11",
                        "resolution_window_artifact_path": str(window_path),
                        "recommendation_id": "rec_existing_01",
                        "summary": "Existing recommendation.",
                        "rationale": "Existing rationale.",
                        "evidence_refs": ["subjective_voice_20260409"],
                        "confidence_score": 0.7,
                        "policy_basis": {
                            "window_dates_considered": ["2026-04-04", "2026-04-10"],
                            "prior_recommendation_refs": [
                                {
                                    "recommendation_id": "rec_window_20260407_walk_01",
                                    "date": "2026-04-07",
                                    "resolution_status": "pending_judgment",
                                }
                            ],
                            "policy_note": "Existing grounded note.",
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode()
            dated_path.write_bytes(original_bytes)
            latest_path.write_bytes(original_bytes)
            payload = self._valid_payload(context_path=context_path, window_path=window_path)
            payload["policy_basis"]["prior_recommendation_refs"][0]["resolution_status"] = "judged"

            result = self._run_cli(["create", "--output-dir", str(health_dir), "--payload-json", json.dumps(payload)], expected_returncode=1)

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "policy_basis_window_inconsistency")
            self.assertTrue(result["error"])
            self.assertEqual(dated_path.read_bytes(), original_bytes)
            self.assertEqual(latest_path.read_bytes(), original_bytes)

    def _valid_payload(self, *, context_path: Path, window_path: Path) -> dict[str, object]:
        return {
            "user_id": "user_dom",
            "date": "2026-04-11",
            "context_artifact_path": str(context_path),
            "context_artifact_id": "agent_context_user_dom_2026-04-11",
            "resolution_window_artifact_path": str(window_path),
            "recommendation_id": "rec_20260411_recovery_01",
            "summary": "Keep today light and prioritize recovery basics.",
            "rationale": "Same-day low-energy context plus the recent window show repeated useful lower-load guidance.",
            "evidence_refs": ["subjective_voice_20260409", "manual_gym_session_20260409"],
            "confidence_score": 0.82,
            "policy_basis": {
                "window_dates_considered": ["2026-04-04", "2026-04-10"],
                "prior_recommendation_refs": [
                    {
                        "recommendation_id": "rec_window_20260407_walk_01",
                        "date": "2026-04-07",
                        "resolution_status": "pending_judgment",
                    }
                ],
                "policy_note": "Carry forward the recent lower-load pattern without introducing hidden memory.",
            },
        }

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_recommendation_cli", *args],
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
