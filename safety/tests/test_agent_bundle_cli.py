from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from health_model.shared_input_backbone import validate_shared_input_bundle


REPO_ROOT = Path(__file__).resolve().parents[1]


class AgentBundleCliIntegrationTest(unittest.TestCase):
    def test_init_creates_canonical_empty_bundle_from_zero_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(temp_dir) / "data" / "health" / "shared_input_bundle_2026-04-10.json"

            result = self._run_cli(
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

            self.assertTrue(result["ok"], msg=result)
            self.assertEqual(result["bundle_path"], str(bundle_path))
            self.assertEqual(
                result["bundle"],
                {
                    "source_artifacts": [],
                    "input_events": [],
                    "subjective_daily_entries": [],
                    "manual_log_entries": [],
                },
            )
            self.assertIsNone(result["error"])
            self.assertTrue(result["validation"]["is_valid"])
            self.assertTrue(bundle_path.exists())

            persisted_bundle = json.loads(bundle_path.read_text())
            self.assertEqual(persisted_bundle, result["bundle"])

            validation = validate_shared_input_bundle(persisted_bundle)
            self.assertTrue(validation.is_valid)

    def test_init_rejects_existing_path_without_mutation(self) -> None:
        existing_bundle = {
            "source_artifacts": [],
            "input_events": [],
            "subjective_daily_entries": [],
            "manual_log_entries": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(temp_dir) / "data" / "health" / "shared_input_bundle_2026-04-10.json"
            bundle_path.parent.mkdir(parents=True, exist_ok=True)
            bundle_path.write_text(json.dumps(existing_bundle, indent=2, sort_keys=True) + "\n")
            original_text = bundle_path.read_text()

            result = self._run_cli(
                [
                    "init",
                    "--bundle-path",
                    str(bundle_path),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-10",
                ],
                expected_returncode=1,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["bundle_path"], str(bundle_path))
            self.assertIsNone(result["bundle"])
            self.assertFalse(result["validation"]["is_valid"])
            self.assertEqual(result["error"]["code"], "bundle_path_exists")
            self.assertEqual(bundle_path.read_text(), original_text)

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
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


if __name__ == "__main__":
    unittest.main()
