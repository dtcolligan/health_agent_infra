from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from health_model.day_nutrition_brief import build_day_nutrition_brief


ROOT_DIR = Path(__file__).resolve().parent.parent
RETRIEVAL_FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures" / "retrieval_contract"


class DayNutritionBriefTest(unittest.TestCase):
    def _write_export_files(self, export_dir: Path) -> None:
        (export_dir / "daily_summary_export.csv").write_text(
            "date,sleep_deep_sec,sleep_light_sec,sleep_rem_sec,sleep_awake_sec,sleep_score_overall,avg_sleep_respiration,awake_count,training_readiness_level,training_recovery_time_hours,training_readiness_sleep_pct,training_readiness_hrv_pct,training_readiness_stress_pct,training_readiness_load_pct,resting_hr,health_hrv_status,body_battery\n"
            "2026-04-08,3600,14400,5400,1200,82,14.2,2,HIGH,12,80,75,65,70,48,balanced,78\n"
        )
        (export_dir / "activities_export.csv").write_text("activity_id,start_time_local\n")

    def test_build_day_nutrition_brief_exposes_truthful_scoped_totals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export_dir = root / "export"
            export_dir.mkdir()
            self._write_export_files(export_dir)

            db_path = root / "health_log.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE daily_summary (
                    user_id INTEGER NOT NULL,
                    date_for TEXT NOT NULL,
                    total_calories REAL,
                    total_protein_g REAL,
                    total_carbs_g REAL,
                    total_fat_g REAL,
                    total_fiber_g REAL,
                    meal_count INTEGER
                );

                CREATE TABLE meal_items (
                    user_id INTEGER NOT NULL,
                    date_for TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    calories REAL,
                    protein_g REAL,
                    carbs_g REAL,
                    fat_g REAL,
                    fiber_g REAL
                );
                """
            )
            conn.executemany(
                "INSERT INTO daily_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (1, "2026-04-08", 1800, 140, 170, 60, 28, 3),
                    (2, "2026-04-08", 2900, 210, 260, 110, 35, 4),
                ],
            )
            conn.executemany(
                "INSERT INTO meal_items VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (1, "2026-04-08", "Oats", 500, 20, 80, 10, 8),
                    (1, "2026-04-08", "Chicken Bowl", 700, 55, 60, 20, 6),
                    (1, "2026-04-08", "Yogurt", 300, 25, 20, 5, 0),
                    (2, "2026-04-08", "Burger", 1200, 40, 90, 70, 3),
                ],
            )
            conn.commit()
            conn.close()

            brief = build_day_nutrition_brief(
                export_dir=export_dir,
                gym_log_path=root / "missing_gym.json",
                db_path=db_path,
                date="2026-04-08",
                user_id=1,
            )

            self.assertEqual(brief["artifact_type"], "day_nutrition_brief")
            self.assertEqual(brief["coverage_status"], "nutrition_available")
            self.assertEqual(brief["nutrition"]["calories_kcal"], 1800.0)
            self.assertEqual(brief["nutrition"]["protein_g"], 140.0)
            self.assertEqual(brief["nutrition"]["carbs_g"], 170.0)
            self.assertEqual(brief["nutrition"]["fat_g"], 60.0)
            self.assertEqual(brief["nutrition"]["fiber_g"], 28.0)
            self.assertEqual(brief["nutrition"]["meal_count"], 3)
            self.assertIn("Chicken Bowl", brief["nutrition"]["top_meals_summary"])
            self.assertNotIn("Burger", brief["nutrition"]["top_meals_summary"])
            self.assertIn("bedtime guidance", " ".join(brief["unsupported_notes"]).lower())
            self.assertIn("micronutrient", " ".join(brief["unsupported_notes"]).lower())

    def test_build_day_nutrition_brief_keeps_missing_nutrition_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export_dir = root / "export"
            export_dir.mkdir()
            self._write_export_files(export_dir)

            brief = build_day_nutrition_brief(
                export_dir=export_dir,
                gym_log_path=root / "missing_gym.json",
                db_path=root / "missing_health_log.db",
                date="2026-04-08",
                user_id=1,
            )

            self.assertEqual(brief["coverage_status"], "nutrition_unavailable")
            self.assertIsNone(brief["nutrition"]["calories_kcal"])
            self.assertIsNone(brief["nutrition"]["protein_g"])
            self.assertIn("does not guess", brief["coverage_note"])

    def test_retrieve_day_nutrition_brief_returns_success_envelope_grounded_in_day_artifact(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "day_nutrition_brief_success_request.json").read_text())
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "day_nutrition_brief_success_response.json").read_text())

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "health_model.day_nutrition_brief",
                "retrieve-day-nutrition-brief",
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
                "--include-missingness",
                "true",
            ],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(json.loads(result.stdout), expected)

    def test_retrieve_day_nutrition_brief_fails_closed_on_wrong_date(self) -> None:
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "day_nutrition_brief_success_request.json").read_text())
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "day_nutrition_brief_wrong_scope_response.json").read_text())

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "health_model.day_nutrition_brief",
                "retrieve-day-nutrition-brief",
                "--artifact-path",
                str((ROOT_DIR / request_fixture["artifact_path"]).resolve()),
                "--user-id",
                request_fixture["user_id"],
                "--date",
                "2026-04-09",
                "--request-id",
                "req_day_nutrition_brief_wrong_date_2026_04_11",
                "--requested-at",
                request_fixture["requested_at"],
            ],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
        self.assertEqual(json.loads(result.stdout), expected)

    def test_cli_writes_dated_artifact_and_latest_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export_dir = root / "export"
            output_dir = root / "out"
            export_dir.mkdir()
            self._write_export_files(export_dir)

            db_path = root / "health_log.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE daily_summary (
                    user_id INTEGER NOT NULL,
                    date_for TEXT NOT NULL,
                    total_calories REAL,
                    total_protein_g REAL,
                    total_carbs_g REAL,
                    total_fat_g REAL,
                    total_fiber_g REAL,
                    meal_count INTEGER
                );
                """
            )
            conn.execute(
                "INSERT INTO daily_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (1, "2026-04-08", 1800, 140, 170, 60, 28, 3),
            )
            conn.commit()
            conn.close()

            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "health_model.day_nutrition_brief",
                    "--date",
                    "2026-04-08",
                    "--user-id",
                    "1",
                    "--export-dir",
                    str(export_dir),
                    "--gym-log-path",
                    str(root / "missing_gym.json"),
                    "--db-path",
                    str(db_path),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            dated_path = output_dir / "day_nutrition_brief_2026-04-08.json"
            latest_path = output_dir / "day_nutrition_brief_latest.json"
            self.assertTrue(dated_path.exists())
            self.assertTrue(latest_path.exists())
            self.assertEqual(json.loads(dated_path.read_text()), json.loads(latest_path.read_text()))


if __name__ == "__main__":
    unittest.main()
