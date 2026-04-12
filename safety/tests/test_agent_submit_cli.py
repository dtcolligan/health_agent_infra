from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from health_model.agent_interface import load_persisted_bundle, write_persisted_bundle


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readable_daily_context"
REPO_ROOT = Path(__file__).resolve().parents[1]


class AgentSubmitCliIntegrationTest(unittest.TestCase):
    def test_cli_submits_hydration_and_meal_and_rejects_wrong_day_without_mutation(self) -> None:
        base_bundle = json.loads((FIXTURE_DIR / "fixture_multi_day_bundle.json").read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            write_persisted_bundle(bundle_path=str(bundle_path), bundle=base_bundle)

            hydration = self._run_cli(
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
                    "--notes",
                    "Evening refill after training.",
                ]
            )
            meal = self._run_cli(
                [
                    "meal",
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-09",
                    "--collected-at",
                    "2026-04-09T20:10:00+01:00",
                    "--ingested-at",
                    "2026-04-09T20:10:04+01:00",
                    "--raw-location",
                    "healthlab://manual/nutrition/2026-04-09/dinner",
                    "--confidence-score",
                    "0.94",
                    "--completeness-state",
                    "complete",
                    "--note-text",
                    "Chicken rice bowl and fruit after run.",
                    "--meal-label",
                    "dinner",
                    "--estimated",
                    "true",
                ]
            )

            original_bundle_text = bundle_path.read_text()
            wrong_day = self._run_cli(
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
                    "2026-04-08T21:00:00+01:00",
                    "--ingested-at",
                    "2026-04-08T21:00:02+01:00",
                    "--raw-location",
                    "healthlab://manual/hydration/2026-04-08/night",
                    "--confidence-score",
                    "0.93",
                    "--completeness-state",
                    "complete",
                    "--amount-ml",
                    "300",
                    "--beverage-type",
                    "water",
                    "--notes",
                    "Wrong-day control fragment.",
                ],
                expected_returncode=1,
            )

            self.assertTrue(hydration["ok"], msg=hydration)
            self.assertTrue(meal["ok"], msg=meal)
            self.assertFalse(wrong_day["ok"])
            self.assertEqual(wrong_day["error"]["code"], "bundle_fragment_scope_mismatch")
            self.assertIn("source_artifact_ids", hydration["accepted_provenance"])
            self.assertIn("input_event_ids", hydration["accepted_provenance"])
            self.assertIn("subjective_entry_ids", hydration["accepted_provenance"])
            self.assertIn("manual_log_entry_ids", hydration["accepted_provenance"])
            self.assertIn("source_artifact_ids", meal["accepted_provenance"])
            self.assertIn("subjective_entry_ids", meal["accepted_provenance"])
            self.assertTrue(hydration["dated_artifact_path"].endswith("agent_readable_daily_context_2026-04-09.json"))
            self.assertTrue(meal["latest_artifact_path"].endswith("agent_readable_daily_context_latest.json"))

            persisted_bundle = load_persisted_bundle(bundle_path=str(bundle_path))
            persisted_manual_ids = {entry["entry_id"] for entry in persisted_bundle["manual_log_entries"]}
            self.assertEqual(bundle_path.read_text(), original_bundle_text)
            self.assertGreaterEqual(len(hydration["accepted_provenance"]["source_artifact_ids"]), 1)
            self.assertGreaterEqual(len(meal["accepted_provenance"]["input_event_ids"]), 1)
            self.assertTrue(any(entry_id in persisted_manual_ids for entry_id in hydration["accepted_provenance"]["manual_log_entry_ids"]))
            self.assertTrue(any(entry_id in persisted_manual_ids for entry_id in meal["accepted_provenance"]["manual_log_entry_ids"]))
            self.assertEqual(wrong_day["accepted_provenance"], {})

    def test_cli_rejects_unsupported_command_with_json_error_envelope(self) -> None:
        rejected = self._run_cli(
            [
                "sleep",
                "--bundle-path",
                "ignored.json",
            ],
            expected_returncode=1,
        )

        self.assertFalse(rejected["ok"])
        self.assertIsNone(rejected["bundle_path"])
        self.assertEqual(rejected["error"]["code"], "cli_parse_error")
        self.assertIn("invalid choice", rejected["error"]["message"])
        self.assertIn("sleep", rejected["error"]["details"]["argv"])
        self.assertEqual(rejected["accepted_provenance"], {})
        self.assertFalse(rejected["validation"]["is_valid"])

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_submit_cli", *args],
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
