from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "voice_note_intake"
VOICE_NOTE_FIXTURE = FIXTURE_DIR / "daily_voice_note_input.json"


class AgentVoiceNoteCliIntegrationTest(unittest.TestCase):
    def test_cli_submits_voice_note_and_regenerates_context_with_subjective_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"

            bootstrap = self._run_module(
                "health_model.agent_bundle_cli",
                [
                    "init",
                    "--bundle-path",
                    str(bundle_path),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                ],
            )
            submit = self._run_cli(
                [
                    "submit",
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                    "--payload-path",
                    str(VOICE_NOTE_FIXTURE),
                ]
            )

            self.assertTrue(bootstrap["ok"], msg=bootstrap)
            self.assertTrue(submit["ok"], msg=submit)
            self.assertEqual(
                submit["accepted_provenance"],
                {
                    "source_artifact_ids": ["artifact_01JQVOICEINTAKE01"],
                    "input_event_ids": ["event_01JQVOICECAF1", "event_01JQVOICELEGS1"],
                    "subjective_entry_ids": ["subjective_01JQVOICESUBJ01"],
                    "manual_log_entry_ids": [],
                },
            )

            dated_artifact = json.loads(Path(submit["dated_artifact_path"]).read_text())
            latest_artifact = json.loads(Path(submit["latest_artifact_path"]).read_text())
            self.assertEqual(dated_artifact, latest_artifact)
            self.assertIn("artifact_01JQVOICEINTAKE01", dated_artifact["generated_from"]["source_artifact_ids"])
            self.assertIn("event_01JQVOICECAF1", dated_artifact["generated_from"]["input_event_ids"])
            self.assertIn("event_01JQVOICELEGS1", dated_artifact["generated_from"]["input_event_ids"])
            self.assertEqual(dated_artifact["generated_from"]["subjective_entry_ids"], ["subjective_01JQVOICESUBJ01"])

    def test_cli_rejects_scope_mismatch_without_mutating_bundle_or_context_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            self._run_module(
                "health_model.agent_bundle_cli",
                [
                    "init",
                    "--bundle-path",
                    str(bundle_path),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                ],
            )
            self._run_cli(
                [
                    "submit",
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                    "--payload-path",
                    str(VOICE_NOTE_FIXTURE),
                ]
            )

            original_bundle = bundle_path.read_bytes()
            dated_path = health_dir / "agent_readable_daily_context_2026-04-09.json"
            latest_path = health_dir / "agent_readable_daily_context_latest.json"
            original_dated = dated_path.read_bytes()
            original_latest = latest_path.read_bytes()

            wrong_day_payload = json.loads(VOICE_NOTE_FIXTURE.read_text())
            wrong_day_payload["derived_events"][0]["effective_date"] = "2026-04-08"
            wrong_day = self._run_cli(
                [
                    "submit",
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                    "--payload-json",
                    json.dumps(wrong_day_payload),
                ],
                expected_returncode=1,
            )

            self.assertFalse(wrong_day["ok"])
            self.assertEqual(wrong_day["error"]["code"], "bundle_fragment_scope_mismatch")
            self.assertEqual(bundle_path.read_bytes(), original_bundle)
            self.assertEqual(dated_path.read_bytes(), original_dated)
            self.assertEqual(latest_path.read_bytes(), original_latest)

    def test_cli_rejects_invalid_payload_without_mutating_bundle_or_context_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            self._run_module(
                "health_model.agent_bundle_cli",
                [
                    "init",
                    "--bundle-path",
                    str(bundle_path),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                ],
            )
            self._run_cli(
                [
                    "submit",
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                    "--payload-path",
                    str(VOICE_NOTE_FIXTURE),
                ]
            )

            original_bundle = bundle_path.read_bytes()
            dated_path = health_dir / "agent_readable_daily_context_2026-04-09.json"
            latest_path = health_dir / "agent_readable_daily_context_latest.json"
            original_dated = dated_path.read_bytes()
            original_latest = latest_path.read_bytes()

            invalid_payload = json.loads(VOICE_NOTE_FIXTURE.read_text())
            invalid_payload["derived_events"][0]["value"] = "true"
            rejected = self._run_cli(
                [
                    "submit",
                    "--bundle-path",
                    str(bundle_path),
                    "--output-dir",
                    str(health_dir),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                    "--payload-json",
                    json.dumps(invalid_payload),
                ],
                expected_returncode=1,
            )

            self.assertFalse(rejected["ok"])
            self.assertEqual(rejected["error"]["code"], "invalid_voice_note_payload")
            self.assertEqual(bundle_path.read_bytes(), original_bundle)
            self.assertEqual(dated_path.read_bytes(), original_dated)
            self.assertEqual(latest_path.read_bytes(), original_latest)

    def test_cli_rejects_malformed_json_with_fail_closed_envelope(self) -> None:
        rejected = self._run_cli(
            [
                "submit",
                "--bundle-path",
                "ignored.json",
                "--output-dir",
                "ignored-dir",
                "--user-id",
                "user_dom",
                "--date",
                "2026-04-09",
                "--payload-json",
                "{",
            ],
            expected_returncode=1,
        )

        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["error"]["code"], "invalid_payload_json")
        self.assertEqual(rejected["accepted_provenance"], {})
        self.assertFalse(rejected["validation"]["is_valid"])
        self.assertEqual(rejected["dated_artifact_path"], None)
        self.assertEqual(rejected["latest_artifact_path"], None)

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        return self._run_module("health_model.agent_voice_note_cli", args, expected_returncode=expected_returncode)

    def _run_module(self, module: str, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", module, *args],
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
