from __future__ import annotations

import json
from pathlib import Path
import unittest

from health_model.shared_input_backbone import shared_input_bundle_json_schema, validate_shared_input_bundle


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "shared_input_backbone"


class SharedInputBackboneTest(unittest.TestCase):
    def test_valid_bundle_covers_wearable_voice_and_manual_inputs(self) -> None:
        result = validate_shared_input_bundle(_load_fixture("valid_bundle.json"))

        self.assertTrue(result.is_valid)
        self.assertEqual(result.schema_issues, [])
        self.assertEqual(result.semantic_issues, [])
        self.assertEqual(len(result.bundle.source_artifacts), 3)
        self.assertEqual(len(result.bundle.input_events), 3)
        self.assertEqual(len(result.bundle.manual_log_entries), 2)

    def test_schema_surface_exposes_only_the_four_canonical_object_families(self) -> None:
        schema = shared_input_bundle_json_schema()

        self.assertEqual(
            set(schema["properties"].keys()),
            {"source_artifacts", "input_events", "subjective_daily_entries", "manual_log_entries"},
        )
        self.assertFalse(schema["additionalProperties"])

    def test_invalid_linkage_is_rejected(self) -> None:
        result = validate_shared_input_bundle(_load_fixture("invalid_linkage_bundle.json"))

        self.assertFalse(result.is_valid)
        self.assertIn("missing_artifact_link", {issue.code for issue in result.semantic_issues})

    def test_invalid_value_field_exclusivity_is_rejected(self) -> None:
        result = validate_shared_input_bundle(_load_fixture("invalid_value_semantics_bundle.json"))

        self.assertFalse(result.is_valid)
        self.assertIn("value_field_exclusivity_violation", {issue.code for issue in result.semantic_issues})

    def test_invalid_manual_payload_optional_typed_fields_are_rejected(self) -> None:
        result = validate_shared_input_bundle(_load_fixture("invalid_manual_payload_bundle.json"))

        self.assertFalse(result.is_valid)
        self.assertIn("invalid_manual_payload_shape", {issue.code for issue in result.semantic_issues})

    def test_invalid_subjective_constraints_are_rejected(self) -> None:
        result = validate_shared_input_bundle(_load_fixture("invalid_subjective_constraints_bundle.json"))

        self.assertFalse(result.is_valid)
        self.assertTrue(
            {"failed_subjective_has_ratings", "failed_subjective_high_confidence"}.issubset(
                {issue.code for issue in result.semantic_issues}
            )
        )

    def test_voice_backed_extraction_requires_transcript_ref(self) -> None:
        result = validate_shared_input_bundle(_load_fixture("invalid_missing_transcript_bundle.json"))

        self.assertFalse(result.is_valid)
        self.assertIn("missing_transcript_ref", {issue.code for issue in result.semantic_issues})

    def test_confidence_threshold_mapping_is_enforced(self) -> None:
        bundle = _load_fixture("valid_bundle.json")
        bundle["manual_log_entries"][0]["confidence_label"] = "medium"

        result = validate_shared_input_bundle(bundle)

        self.assertFalse(result.is_valid)
        self.assertIn("confidence_label_score_mismatch", {issue.code for issue in result.semantic_issues})

    def test_duplicate_primary_ids_are_rejected_within_object_families(self) -> None:
        result = validate_shared_input_bundle(_load_fixture("invalid_duplicate_ids_bundle.json"))

        self.assertFalse(result.is_valid)
        self.assertIn("duplicate_primary_id", {issue.code for issue in result.semantic_issues})


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_DIR / name).read_text())


if __name__ == "__main__":
    unittest.main()
