from __future__ import annotations

import json
from pathlib import Path
import unittest

from health_model.shared_input_backbone import validate_shared_input_bundle
from health_model.voice_note_intake import canonicalize_voice_note_payload


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "voice_note_intake"


class VoiceNoteIntakeTest(unittest.TestCase):
    def test_fixture_voice_note_canonicalizes_without_schema_drift(self) -> None:
        payload = _load_fixture("daily_voice_note_input.json")
        expected_bundle = _load_fixture("daily_voice_note_expected_bundle.json")

        bundle = canonicalize_voice_note_payload(payload)
        validation = validate_shared_input_bundle(bundle)

        self.assertEqual(bundle, expected_bundle)
        self.assertTrue(validation.is_valid)
        self.assertEqual(validation.schema_issues, [])
        self.assertEqual(validation.semantic_issues, [])

    def test_voice_note_events_and_subjective_entry_keep_artifact_provenance(self) -> None:
        bundle = canonicalize_voice_note_payload(_load_fixture("daily_voice_note_input.json"))

        artifact_id = bundle["source_artifacts"][0]["artifact_id"]
        self.assertTrue(all(event["provenance"]["artifact_id"] == artifact_id for event in bundle["input_events"]))
        self.assertEqual(bundle["subjective_daily_entries"][0]["source_artifact_ids"], [artifact_id])
        self.assertTrue(all(event["provenance"]["supporting_refs"] for event in bundle["input_events"]))

    def test_missing_voice_note_value_is_explicit_and_validated(self) -> None:
        payload = _load_fixture("daily_voice_note_input.json")
        payload["derived_events"].append(
            {
                "event_id": "event_01JQVOICEHYDRO1",
                "source_record_id": "segment_15",
                "domain": "hydration",
                "metric_name": "hydration_amount_ml",
                "value_type": "number",
                "effective_date": "2026-04-09",
                "confidence_score": 0.41,
                "missingness_state": "missing_not_provided",
                "uncertainty_note": "Hydration was discussed but no amount was stated.",
                "supporting_refs": ["transcript:chars:146-171"]
            }
        )

        bundle = canonicalize_voice_note_payload(payload)
        validation = validate_shared_input_bundle(bundle)
        missing_event = bundle["input_events"][-1]

        self.assertEqual(missing_event["missingness_state"], "missing_not_provided")
        self.assertEqual(missing_event["confidence_label"], "low")
        self.assertIsNone(missing_event["event_start_at"])
        self.assertIsNone(missing_event["event_end_at"])
        self.assertNotIn("value_number", missing_event)
        self.assertTrue(validation.is_valid)


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_DIR / name).read_text())


if __name__ == "__main__":
    unittest.main()
