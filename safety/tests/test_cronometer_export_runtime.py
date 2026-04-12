from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pull.cronometer.connector import run_connector

FIXTURES = Path(__file__).resolve().parents[2] / "pull" / "cronometer" / "fixtures"


class CronometerExportRuntimeTest(unittest.TestCase):
    def test_replay_is_stable_for_same_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            output = root / "out"
            work = root / "work"

            first = run_connector(FIXTURES / "daily_nutrition_baseline.csv", state, output, work)
            second = run_connector(FIXTURES / "daily_nutrition_baseline.csv", state, output, work)

            self.assertEqual(first["run_id"], second["run_id"])
            self.assertEqual(second["processed_dates"], [])
            first_payload = json.loads((output / "2026-04-09" / "nutrition_daily.json").read_text())
            second_payload = json.loads((output / "2026-04-09" / "nutrition_daily.json").read_text())
            self.assertEqual(first_payload["nutrition_daily_id"], second_payload["nutrition_daily_id"])

    def test_overlap_replay_only_processes_changed_or_new_days(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            output = root / "out"
            work = root / "work"

            run_connector(FIXTURES / "daily_nutrition_baseline.csv", state, output, work)
            follow = run_connector(FIXTURES / "daily_nutrition_followup.csv", state, output, work)

            self.assertEqual(follow["target_dates"], ["2026-04-08", "2026-04-09", "2026-04-10", "2026-04-11"])
            self.assertEqual(follow["processed_dates"], ["2026-04-09", "2026-04-11"])
            updated = json.loads((output / "2026-04-09" / "nutrition_daily.json").read_text())
            self.assertEqual(updated["calories_kcal"], 2110.0)

    def test_resume_continues_from_first_incomplete_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            output = root / "out"
            work = root / "work"

            run_connector(FIXTURES / "daily_nutrition_baseline.csv", state, output, work)
            interrupted = run_connector(FIXTURES / "daily_nutrition_followup.csv", state, output, work, stop_after_days=1)
            self.assertTrue(interrupted["interrupted"])
            resumed = run_connector(FIXTURES / "daily_nutrition_followup.csv", state, output, work, resume=True)
            self.assertFalse(resumed["interrupted"])
            self.assertEqual(resumed["processed_dates"], ["2026-04-11"])

            snapshot = json.loads(state.read_text())
            self.assertEqual(snapshot["slice_status"][resumed["run_id"]]["2026-04-09"], "completed")
            self.assertEqual(snapshot["slice_status"][resumed["run_id"]]["2026-04-11"], "completed")


if __name__ == "__main__":
    unittest.main()
