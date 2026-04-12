from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from health_model.agent_interface import append_fragment_and_regenerate_daily_context
from health_model.voice_note_intake import canonicalize_voice_note_payload


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "manual_subjective_recovery"


class ManualSubjectiveRecoveryContractTest(unittest.TestCase):
    def test_complete_subjective_payload_emits_stable_ids(self) -> None:
        payload = _load_fixture("complete_voice_note_payload.json")
        expected_ids = _load_fixture("replay_expected_ids.json")

        bundle = canonicalize_voice_note_payload(payload)
        subjective_entry = bundle["subjective_daily_entries"][0]

        self.assertEqual(subjective_entry["source_record_id"], expected_ids["source_record_id"])
        self.assertEqual(subjective_entry["provenance_record_id"], expected_ids["provenance_record_id"])
        self.assertEqual(subjective_entry["entry_id"], expected_ids["entry_id"])
        self.assertEqual(subjective_entry["source_name"], "manual_subjective_recovery")

    def test_partial_subjective_payload_keeps_missingness_explicit(self) -> None:
        payload = _load_fixture("partial_subjective_payload.json")

        bundle = canonicalize_voice_note_payload(payload)
        subjective_entry = bundle["subjective_daily_entries"][0]

        self.assertEqual(subjective_entry["extraction_status"], "partial")
        self.assertEqual(subjective_entry["energy_self_rating"], 2)
        self.assertNotIn("stress_self_rating", subjective_entry)
        self.assertNotIn("mood_self_rating", subjective_entry)
        self.assertNotIn("perceived_sleep_quality", subjective_entry)

    def test_conflict_subjective_payload_keeps_conflict_explicit_in_downstream_context(self) -> None:
        payload = _load_fixture("conflict_subjective_payload.json")
        fragment = canonicalize_voice_note_payload(payload)
        base_bundle = {
            "source_artifacts": [],
            "input_events": [],
            "subjective_daily_entries": [],
            "manual_log_entries": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(temp_dir) / "shared_input_bundle_2026-04-09.json"
            bundle_path.write_text(json.dumps(base_bundle, indent=2))
            result = append_fragment_and_regenerate_daily_context(
                bundle_path=str(bundle_path),
                output_dir=temp_dir,
                fragment=fragment,
                user_id="user_dom",
                date="2026-04-09",
            )

            self.assertTrue(result["ok"], msg=result)
            artifact = json.loads(Path(result["dated_artifact_path"]).read_text())
            perceived_recovery_signal = next(
                signal
                for signal in artifact["explicit_grounding"]["signals"]
                if signal["domain"] == "subjective_state" and signal["signal_key"] == "perceived_recovery"
            )
            self.assertEqual(perceived_recovery_signal["status"], "conflicted")
            self.assertIn("conflicting_perceived_recovery", {conflict["code"] for conflict in artifact["conflicts"]})


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text())


if __name__ == "__main__":
    unittest.main()
