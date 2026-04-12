from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from health_model.agent_interface import write_persisted_bundle


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readable_daily_context"
REPO_ROOT = Path(__file__).resolve().parents[1]


class AgentContextCliIntegrationTest(unittest.TestCase):
    def test_get_reads_valid_scoped_context_after_zero_to_one_init_submit_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-10.json"

            init = self._run_bundle_cli(
                [
                    "init",
                    "--bundle-path",
                    str(bundle_path),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-10",
                ]
            )

            submit = self._run_submit_cli(
                [
                    "hydration",
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-10",
                    "--collected-at",
                    "2026-04-10T09:15:00+01:00",
                    "--ingested-at",
                    "2026-04-10T09:15:03+01:00",
                    "--raw-location",
                    "healthlab://manual/hydration/2026-04-10/morning",
                    "--confidence-score",
                    "0.99",
                    "--completeness-state",
                    "complete",
                    "--amount-ml",
                    "500",
                    "--beverage-type",
                    "water",
                ]
            )

            read_result = self._run_context_cli(
                [
                    "get",
                    "--artifact-path",
                    submit["dated_artifact_path"],
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-10",
                ]
            )

            self.assertTrue(init["ok"], msg=init)
            self.assertTrue(submit["ok"], msg=submit)
            self.assertTrue(read_result["ok"], msg=read_result)
            self.assertEqual(read_result["context"]["artifact_type"], "agent_readable_daily_context")
            self.assertEqual(read_result["context"]["user_id"], "user_1")
            self.assertEqual(read_result["context"]["date"], "2026-04-10")

    def test_get_reads_valid_scoped_context_after_submit_regenerate_flow(self) -> None:
        base_bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            write_persisted_bundle(bundle_path=str(bundle_path), bundle=base_bundle)

            submit = self._run_submit_cli(
                [
                    "hydration",
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-09",
                    "--collected-at",
                    "2026-04-09T18:20:00+01:00",
                    "--ingested-at",
                    "2026-04-09T18:20:03+01:00",
                    "--raw-location",
                    "healthlab://manual/hydration/2026-04-09/evening",
                    "--confidence-score",
                    "0.98",
                    "--completeness-state",
                    "complete",
                    "--amount-ml",
                    "750",
                    "--beverage-type",
                    "water",
                ]
            )
            artifact_path = submit["dated_artifact_path"]

            read_result = self._run_context_cli(
                [
                    "get",
                    "--artifact-path",
                    artifact_path,
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-09",
                ]
            )
            latest_result = self._run_context_cli(
                [
                    "get-latest",
                    "--artifact-path",
                    submit["latest_artifact_path"],
                    "--user-id",
                    "user_1",
                ]
            )

            self.assertTrue(read_result["ok"], msg=read_result)
            self.assertEqual(read_result["artifact_path"], artifact_path)
            self.assertEqual(read_result["context"]["artifact_type"], "agent_readable_daily_context")
            self.assertEqual(read_result["context"]["user_id"], "user_1")
            self.assertEqual(read_result["context"]["date"], "2026-04-09")
            self.assertTrue(latest_result["ok"], msg=latest_result)
            self.assertEqual(latest_result["context"], read_result["context"])

    def test_get_rejects_wrong_scope_with_json_error_envelope(self) -> None:
        artifact_path = FIXTURE_DIR / "generated_fixture_day_context.json"

        result = self._run_context_cli(
            [
                "get",
                "--artifact-path",
                str(artifact_path),
                "--user-id",
                "user_2",
                "--date",
                "2026-04-09",
            ],
            expected_returncode=1,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "artifact_user_mismatch")
        self.assertFalse(result["validation"]["is_valid"])
        self.assertIsNone(result["context"])
        self.assertTrue(any(issue["code"] == "artifact_user_mismatch" for issue in result["validation"]["semantic_issues"]))

    def test_get_rejects_wrong_date_with_json_error_envelope(self) -> None:
        artifact_path = FIXTURE_DIR / "generated_fixture_day_context.json"

        result = self._run_context_cli(
            [
                "get",
                "--artifact-path",
                str(artifact_path),
                "--user-id",
                "user_1",
                "--date",
                "2026-04-08",
            ],
            expected_returncode=1,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "artifact_date_mismatch")
        self.assertFalse(result["validation"]["is_valid"])
        self.assertIsNone(result["context"])
        self.assertTrue(any(issue["code"] == "artifact_date_mismatch" for issue in result["validation"]["semantic_issues"]))

    def test_get_rejects_missing_artifact_with_json_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.json"

            result = self._run_context_cli(
                [
                    "get",
                    "--artifact-path",
                    str(missing_path),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-09",
                ],
                expected_returncode=1,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "artifact_not_found")
        self.assertFalse(result["validation"]["is_valid"])
        self.assertIsNone(result["context"])
        self.assertTrue(any(issue["code"] == "artifact_not_found" for issue in result["validation"]["semantic_issues"]))

    def test_get_rejects_invalid_artifact_json_with_json_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "invalid.json"
            invalid_path.write_text("not valid json\n")

            result = self._run_context_cli(
                [
                    "get",
                    "--artifact-path",
                    str(invalid_path),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-09",
                ],
                expected_returncode=1,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_artifact_json")
        self.assertIsNone(result["context"])
        self.assertTrue(any(issue["code"] == "invalid_artifact_json" for issue in result["validation"]["semantic_issues"]))

    def test_get_rejects_artifact_type_mismatch_with_json_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "wrong_type.json"
            invalid_path.write_text(json.dumps({"artifact_type": "not_daily_context", "user_id": "user_1", "date": "2026-04-09"}))

            result = self._run_context_cli(
                [
                    "get",
                    "--artifact-path",
                    str(invalid_path),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-09",
                ],
                expected_returncode=1,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "artifact_type_mismatch")
        self.assertIsNone(result["context"])
        self.assertTrue(any(issue["code"] == "artifact_type_mismatch" for issue in result["validation"]["semantic_issues"]))

    def _run_submit_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_submit_cli", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected_returncode, msg=completed.stderr or completed.stdout)
        self.assertEqual(completed.stderr.strip(), "")
        return json.loads(completed.stdout)

    def _run_bundle_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_bundle_cli", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected_returncode, msg=completed.stderr or completed.stdout)
        self.assertEqual(completed.stderr.strip(), "")
        self.assertTrue(completed.stdout.strip())
        return json.loads(completed.stdout)

    def _run_context_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_context_cli", *args],
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
