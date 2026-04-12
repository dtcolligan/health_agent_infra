from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readable_daily_context"


class BuildDailyContextArtifactTest(unittest.TestCase):
    def test_fixture_bundle_writes_exact_daily_context_artifact(self) -> None:
        expected = json.loads((FIXTURE_DIR / "generated_fixture_day_context.json").read_text())

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "health_model.build_daily_context_artifact",
                    "--bundle-path",
                    "tests/fixtures/agent_readable_daily_context/fixture_day_bundle.json",
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-09",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)

            dated_path = output_dir / "agent_readable_daily_context_2026-04-09.json"
            latest_path = output_dir / "agent_readable_daily_context_latest.json"
            self.assertEqual(json.loads(dated_path.read_text()), expected)
            self.assertEqual(json.loads(latest_path.read_text()), expected)
            self.assertEqual(dated_path.read_text(), latest_path.read_text())

            signals = json.loads(dated_path.read_text())["explicit_grounding"]["signals"]
            self.assertTrue(any(signal["domain"] == "nutrition" for signal in signals))
            self.assertTrue(any(signal["domain"] == "hydration" for signal in signals))

    def test_invalid_bundle_fails_closed_with_grounded_validation_details(self) -> None:
        invalid_bundle = json.loads((FIXTURE_DIR / "fixture_day_bundle.json").read_text())
        invalid_bundle["manual_log_entries"][0]["source_artifact_id"] = "artifact_missing"

        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "invalid_bundle.json"
            invalid_path.write_text(json.dumps(invalid_bundle))

            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "health_model.build_daily_context_artifact",
                    "--bundle-path",
                    str(invalid_path),
                    "--user-id",
                    "user_1",
                    "--date",
                    "2026-04-09",
                    "--output-dir",
                    str(Path(temp_dir) / "out"),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Shared input bundle failed validation", result.stderr)
            self.assertIn("missing_artifact_link", result.stderr)
            self.assertIn("manual_log_entries[0].source_artifact_id", result.stderr)


if __name__ == "__main__":
    unittest.main()
