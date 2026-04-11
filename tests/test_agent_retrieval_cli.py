from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RETRIEVAL_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "retrieval_contract"


class AgentRetrievalCliIntegrationTest(unittest.TestCase):
    def test_sleep_review_returns_partial_success_envelope_grounded_in_day_context(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "sleep_review_success_request.json").read_text())
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "sleep_review_partial_success_response.json").read_text())

        result = self._run_cli(
            [
                "sleep-review",
                "--artifact-path",
                request_fixture["artifact_path"],
                "--user-id",
                request_fixture["user_id"],
                "--date",
                request_fixture["date"],
                "--request-id",
                request_fixture["request_id"],
                "--requested-at",
                request_fixture["requested_at"],
                "--include-conflicts",
                "true",
                "--include-missingness",
                "true",
            ]
        )

        self.assertTrue(result["ok"], msg=result)
        self.assertEqual(result, expected)

    def test_sleep_review_fails_closed_on_invalid_requested_at_with_request_echo(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "sleep_review_success_request.json").read_text())

        result = self._run_cli(
            [
                "sleep-review",
                "--artifact-path",
                request_fixture["artifact_path"],
                "--user-id",
                request_fixture["user_id"],
                "--date",
                request_fixture["date"],
                "--request-id",
                request_fixture["request_id"],
                "--requested-at",
                "2026-04-11T09:10:00",
            ],
            expected_returncode=1,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_requested_at")
        self.assertEqual(
            result["validation"]["request_echo"],
            {
                "request_id": request_fixture["request_id"],
                "requested_at": "2026-04-11T09:10:00",
            },
        )

    def test_sleep_review_fails_closed_on_wrong_date_with_retrieval_wrapper_envelope(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "sleep_review_success_request.json").read_text())
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "sleep_review_wrong_scope_response.json").read_text())

        result = self._run_cli(
            [
                "sleep-review",
                "--artifact-path",
                str((REPO_ROOT / request_fixture["artifact_path"]).resolve()),
                "--user-id",
                request_fixture["user_id"],
                "--date",
                "2026-04-09",
                "--request-id",
                "req_sleep_review_wrong_date_2026_04_11",
                "--requested-at",
                request_fixture["requested_at"],
            ],
            expected_returncode=1,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result, expected)

    def test_weekly_pattern_review_returns_success_envelope_grounded_in_accepted_daily_artifacts(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "weekly_pattern_review_success_request.json").read_text())
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "weekly_pattern_review_success_response.json").read_text())

        result = self._run_context_cli(
            [
                "retrieve-weekly-pattern-review",
                "--user-id",
                request_fixture["user_id"],
                "--start-date",
                request_fixture["start_date"],
                "--end-date",
                request_fixture["end_date"],
                "--memory-locator",
                request_fixture["memory_locator"],
                "--request-id",
                request_fixture["request_id"],
                "--requested-at",
                request_fixture["requested_at"],
                "--include-conflicts",
                request_fixture["include_conflicts"],
                "--include-missingness",
                request_fixture["include_missingness"],
            ]
        )

        self.assertTrue(result["ok"], msg=result)
        self.assertEqual(result, expected)

    def test_weekly_pattern_review_fails_closed_on_wrong_scope(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "weekly_pattern_review_success_request.json").read_text())
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "weekly_pattern_review_wrong_scope_response.json").read_text())

        result = self._run_context_cli(
            [
                "retrieve-weekly-pattern-review",
                "--user-id",
                "user_wrong",
                "--start-date",
                request_fixture["start_date"],
                "--end-date",
                request_fixture["end_date"],
                "--memory-locator",
                request_fixture["memory_locator"],
                "--request-id",
                "req_weekly_pattern_review_wrong_scope_2026_04_11",
                "--requested-at",
                request_fixture["requested_at"],
            ],
            expected_returncode=1,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result, expected)

    def test_weekly_pattern_review_fails_closed_on_range_limit(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "weekly_pattern_review_success_request.json").read_text())
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "weekly_pattern_review_range_limit_response.json").read_text())

        result = self._run_context_cli(
            [
                "retrieve-weekly-pattern-review",
                "--user-id",
                request_fixture["user_id"],
                "--start-date",
                "2026-04-03",
                "--end-date",
                request_fixture["end_date"],
                "--memory-locator",
                request_fixture["memory_locator"],
                "--request-id",
                "req_weekly_pattern_review_range_limit_2026_04_11",
                "--requested-at",
                request_fixture["requested_at"],
            ],
            expected_returncode=1,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result, expected)

    def test_weekly_pattern_review_fails_closed_on_invalid_requested_at_with_request_echo(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "weekly_pattern_review_success_request.json").read_text())
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "weekly_pattern_review_invalid_request_metadata_response.json").read_text())

        result = self._run_context_cli(
            [
                "retrieve-weekly-pattern-review",
                "--user-id",
                request_fixture["user_id"],
                "--start-date",
                request_fixture["start_date"],
                "--end-date",
                request_fixture["end_date"],
                "--memory-locator",
                request_fixture["memory_locator"],
                "--request-id",
                request_fixture["request_id"],
                "--requested-at",
                "2026-04-11T10:15:00",
            ],
            expected_returncode=1,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result, expected)

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "health_model.agent_retrieval_cli", *args],
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
