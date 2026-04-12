from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VOICE_NOTE_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "voice_note_intake" / "daily_voice_note_input.json"
RETRIEVAL_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "retrieval_contract"


class AgentContractCliIntegrationTest(unittest.TestCase):
    def test_describe_returns_machine_readable_contract_for_bootstrap_submit_context_retrieval_and_recommendation_loop(self) -> None:
        result = self._run_cli(["describe"])

        self.assertTrue(result["ok"], msg=result)
        self.assertIsNone(result["error"])
        self.assertTrue(result["validation"]["is_valid"])

        contract = result["contract"]
        self.assertEqual(contract["contract_id"], "health_lab_agent_contract")
        self.assertEqual(contract["contract_version"], "2026-04-11")
        self.assertEqual(contract["architecture_boundary"]["private_memory_layer"], "external_to_health_lab")
        self.assertFalse(contract["architecture_boundary"]["hosted_memory_claims"])
        self.assertFalse(contract["architecture_boundary"]["embedded_coach_claims"])
        self.assertEqual(contract["discovery"]["command"], "describe")
        self.assertEqual(contract["accepted_enums"]["bundle_commands"], ["init"])
        self.assertEqual(contract["accepted_enums"]["submit_commands"], ["hydration", "meal"])
        self.assertEqual(contract["accepted_enums"]["voice_note_commands"], ["submit"])
        self.assertEqual(contract["accepted_enums"]["voice_note_payload_inputs"], ["payload_json", "payload_path"])
        self.assertEqual(contract["accepted_enums"]["context_commands"], ["get", "get-latest"])
        self.assertEqual(
            contract["accepted_enums"]["retrieval_operations"],
            [
                "retrieve.day_context",
                "retrieve.day_nutrition_brief",
                "retrieve.sleep_review",
                "retrieve.recommendation",
                "retrieve.recommendation_judgment",
                "retrieve.recommendation_feedback",
                "retrieve.recommendation_feedback_window",
                "retrieve.recommendation_resolution_window",
                "retrieve.weekly_pattern_review",
            ],
        )
        self.assertEqual(contract["accepted_enums"]["recommendation_commands"], ["create"])
        self.assertEqual(contract["accepted_enums"]["recommendation_payload_inputs"], ["payload_json", "payload_path"])
        self.assertEqual(contract["accepted_enums"]["writeback_operations"], ["writeback.recommendation_judgment", "writeback.recommendation_resolution_transition"])
        self.assertEqual(contract["accepted_enums"]["writeback_payload_inputs"], ["payload_json", "payload_path"])
        self.assertEqual(contract["accepted_enums"]["judgment_labels"], ["useful", "obvious", "wrong", "ignored"])
        self.assertEqual(contract["accepted_enums"]["completeness_state"], ["partial", "complete", "corrected"])
        self.assertEqual(contract["accepted_enums"]["estimated"], ["true", "false"])
        self.assertEqual(contract["accepted_enums"]["retrieval_boolean_flags"], ["true", "false"])
        self.assertEqual(
            contract["accepted_enums"]["retrieval_missingness_states"],
            ["present", "partial", "missing", "not_supported"],
        )
        self.assertEqual(
            contract["accepted_enums"]["retrieval_conflict_states"],
            ["none", "source_conflict", "scope_conflict", "resolution_required"],
        )
        self.assertIn("request_id", contract["accepted_scope_fields"])
        self.assertIn("requested_at", contract["accepted_scope_fields"])
        self.assertIn("memory_locator", contract["accepted_scope_fields"])
        self.assertEqual(
            contract["path_conventions"]["dated_context_artifact"],
            "{output_dir}/agent_readable_daily_context_{date}.json",
        )
        self.assertEqual(
            contract["path_conventions"]["latest_context_artifact"],
            "{output_dir}/agent_readable_daily_context_latest.json",
        )
        self.assertEqual(
            contract["path_conventions"]["dated_recommendation_artifact"],
            "{output_dir}/agent_recommendation_{date}.json",
        )
        self.assertEqual(
            contract["path_conventions"]["latest_recommendation_artifact"],
            "{output_dir}/agent_recommendation_latest.json",
        )
        self.assertEqual(
            contract["path_conventions"]["dated_recommendation_judgment_artifact"],
            "{output_dir}/recommendation_judgment_{date}.json",
        )
        self.assertEqual(
            contract["path_conventions"]["latest_recommendation_judgment_artifact"],
            "{output_dir}/recommendation_judgment_latest.json",
        )
        self.assertEqual(
            contract["path_conventions"]["dated_recommendation_resolution_window_memory_artifact"],
            "{output_dir}/recommendation_resolution_window_memory_{start_date}_{end_date}.json",
        )
        self.assertEqual(
            contract["path_conventions"]["latest_recommendation_resolution_window_memory_artifact"],
            "{output_dir}/recommendation_resolution_window_memory_latest.json",
        )

        bootstrap_init = contract["supported_operations"]["bootstrap.init"]
        self.assertEqual(bootstrap_init["module"], "health_model.agent_bundle_cli")
        self.assertEqual(bootstrap_init["command"], "init")
        self.assertEqual(bootstrap_init["mode"], "write")
        self.assertEqual([arg["name"] for arg in bootstrap_init["args"]], ["bundle_path", "user_id", "date"])

        submit_hydration = contract["supported_operations"]["submit.hydration"]
        hydration_flags = {arg["flag"] for arg in submit_hydration["args"]}
        self.assertIn("--bundle-path", hydration_flags)
        self.assertIn("--amount-ml", hydration_flags)
        self.assertIn("--beverage-type", hydration_flags)
        self.assertIn("--completeness-state", hydration_flags)

        submit_meal = contract["supported_operations"]["submit.meal"]
        meal_args = {arg["name"]: arg for arg in submit_meal["args"]}
        self.assertEqual(meal_args["estimated"]["accepted_values"], ["true", "false"])
        self.assertTrue(meal_args["note_text"]["required"])
        self.assertFalse(meal_args["meal_label"]["required"])

        submit_voice_note = contract["supported_operations"]["submit.voice_note"]
        voice_note_args = {arg["name"]: arg for arg in submit_voice_note["args"]}
        self.assertEqual(submit_voice_note["module"], "health_model.agent_voice_note_cli")
        self.assertEqual(submit_voice_note["command"], "submit")
        self.assertEqual(submit_voice_note["consumes"], ["shared_input_bundle", "voice_note_submission_payload"])
        self.assertEqual(
            submit_voice_note["produces"],
            ["shared_input_bundle", "agent_readable_daily_context_dated", "agent_readable_daily_context_latest"],
        )
        self.assertEqual(voice_note_args["payload_json"]["type"], "json_object")
        self.assertFalse(voice_note_args["payload_json"]["required"])
        self.assertFalse(voice_note_args["payload_path"]["required"])

        context_get = contract["supported_operations"]["context.get"]
        self.assertEqual(context_get["command"], "get")
        self.assertEqual([arg["name"] for arg in context_get["args"]], ["artifact_path", "user_id", "date"])

        retrieval_day_context = contract["supported_operations"]["retrieve.day_context"]
        retrieval_args = {arg["name"]: arg for arg in retrieval_day_context["args"]}
        self.assertEqual(retrieval_day_context["module"], "health_model.agent_context_cli")
        self.assertEqual(retrieval_day_context["command"], "get")
        self.assertEqual(retrieval_day_context["mode"], "read")
        self.assertEqual(retrieval_day_context["implementation_status"], "proof_complete")
        self.assertEqual(retrieval_day_context["response_envelope"], "retrieval")
        self.assertEqual(retrieval_day_context["consumes"], ["agent_readable_daily_context"])
        self.assertEqual(retrieval_day_context["produces"], ["retrieval_response_envelope"])
        self.assertEqual(retrieval_args["artifact_path"]["flag"], "--artifact-path")
        self.assertEqual(retrieval_args["request_id"]["flag"], "--request-id")
        self.assertNotIn("timezone", retrieval_args)
        self.assertNotIn("max_evidence_items", retrieval_args)

        sleep_review = contract["supported_operations"]["retrieve.sleep_review"]
        sleep_review_args = {arg["name"]: arg for arg in sleep_review["args"]}
        self.assertEqual(sleep_review["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(sleep_review["command"], "sleep-review")
        self.assertEqual(sleep_review["implementation_status"], "proof_complete")
        self.assertEqual(sleep_review["consumes"], ["agent_readable_daily_context"])
        self.assertEqual(sleep_review_args["artifact_path"]["flag"], "--artifact-path")
        self.assertNotIn("timezone", sleep_review_args)
        self.assertNotIn("max_evidence_items", sleep_review_args)

        recommendation = contract["supported_operations"]["retrieve.recommendation"]
        recommendation_args = {arg["name"]: arg for arg in recommendation["args"]}
        self.assertEqual(recommendation["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation["command"], "recommendation")
        self.assertEqual(recommendation["implementation_status"], "proof_complete")
        self.assertEqual(recommendation["consumes"], ["agent_recommendation"])
        self.assertEqual(recommendation_args["artifact_path"]["flag"], "--artifact-path")
        self.assertNotIn("timezone", recommendation_args)
        self.assertNotIn("max_evidence_items", recommendation_args)

        recommendation_judgment = contract["supported_operations"]["retrieve.recommendation_judgment"]
        recommendation_judgment_args = {arg["name"]: arg for arg in recommendation_judgment["args"]}
        self.assertEqual(recommendation_judgment["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation_judgment["command"], "recommendation-judgment")
        self.assertEqual(recommendation_judgment["implementation_status"], "proof_complete")
        self.assertEqual(recommendation_judgment["consumes"], ["recommendation_judgment"])
        self.assertEqual(recommendation_judgment_args["artifact_path"]["flag"], "--artifact-path")
        self.assertNotIn("timezone", recommendation_judgment_args)
        self.assertNotIn("max_evidence_items", recommendation_judgment_args)

        recommendation_feedback = contract["supported_operations"]["retrieve.recommendation_feedback"]
        recommendation_feedback_args = {arg["name"]: arg for arg in recommendation_feedback["args"]}
        self.assertEqual(recommendation_feedback["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation_feedback["command"], "recommendation-feedback")
        self.assertEqual(recommendation_feedback["implementation_status"], "proof_complete")
        self.assertEqual(recommendation_feedback["consumes"], ["agent_recommendation", "recommendation_judgment"])
        self.assertEqual(recommendation_feedback_args["recommendation_artifact_path"]["flag"], "--recommendation-artifact-path")
        self.assertEqual(recommendation_feedback_args["judgment_artifact_path"]["flag"], "--judgment-artifact-path")
        self.assertNotIn("timezone", recommendation_feedback_args)
        self.assertNotIn("max_evidence_items", recommendation_feedback_args)

        recommendation_feedback_window = contract["supported_operations"]["retrieve.recommendation_feedback_window"]
        recommendation_feedback_window_args = {arg["name"]: arg for arg in recommendation_feedback_window["args"]}
        self.assertEqual(recommendation_feedback_window["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation_feedback_window["command"], "recommendation-feedback-window")
        self.assertEqual(recommendation_feedback_window["implementation_status"], "proof_complete")
        self.assertEqual(recommendation_feedback_window["range_limit_days"], 7)
        self.assertEqual(
            recommendation_feedback_window["consumes"],
            ["user_owned_private_memory_locator", "agent_recommendation", "recommendation_judgment"],
        )
        self.assertEqual(recommendation_feedback_window_args["memory_locator"]["flag"], "--memory-locator")
        self.assertEqual(recommendation_feedback_window_args["max_feedback_items"]["flag"], "--max-feedback-items")

        recommendation_resolution_window = contract["supported_operations"]["retrieve.recommendation_resolution_window"]
        recommendation_resolution_window_args = {arg["name"]: arg for arg in recommendation_resolution_window["args"]}
        self.assertEqual(recommendation_resolution_window["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation_resolution_window["command"], "recommendation-resolution-window")
        self.assertEqual(recommendation_resolution_window["implementation_status"], "proof_complete")
        self.assertEqual(recommendation_resolution_window["range_limit_days"], 7)
        self.assertEqual(
            recommendation_resolution_window["consumes"],
            ["user_owned_private_memory_locator", "agent_recommendation", "recommendation_judgment"],
        )
        self.assertEqual(recommendation_resolution_window_args["memory_locator"]["flag"], "--memory-locator")
        self.assertEqual(recommendation_resolution_window_args["max_recommendation_items"]["flag"], "--max-recommendation-items")

        day_nutrition_brief = contract["supported_operations"]["retrieve.day_nutrition_brief"]
        day_nutrition_args = {arg["name"]: arg for arg in day_nutrition_brief["args"]}
        self.assertEqual(day_nutrition_brief["module"], "health_model.day_nutrition_brief")
        self.assertEqual(day_nutrition_brief["command"], "retrieve-day-nutrition-brief")
        self.assertEqual(day_nutrition_brief["implementation_status"], "proof_complete")
        self.assertEqual(day_nutrition_brief["consumes"], ["day_nutrition_brief"])
        self.assertEqual(day_nutrition_args["artifact_path"]["flag"], "--artifact-path")
        self.assertNotIn("timezone", day_nutrition_args)
        self.assertNotIn("max_evidence_items", day_nutrition_args)

        weekly_review = contract["supported_operations"]["retrieve.weekly_pattern_review"]
        weekly_args = {arg["name"]: arg for arg in weekly_review["args"]}
        self.assertEqual(weekly_review["implementation_status"], "proof_complete")
        self.assertEqual(weekly_review["range_limit_days"], 7)
        self.assertEqual(weekly_review["command"], "retrieve-weekly-pattern-review")
        self.assertEqual(weekly_review["consumes"], ["user_owned_private_memory_locator", "agent_readable_daily_context"])
        self.assertEqual(weekly_args["start_date"]["flag"], "--start-date")
        self.assertEqual(weekly_args["end_date"]["flag"], "--end-date")
        self.assertEqual(weekly_args["memory_locator"]["flag"], "--memory-locator")

        recommendation_create = contract["supported_operations"]["recommendation.create"]
        recommendation_args = {arg["name"]: arg for arg in recommendation_create["args"]}
        self.assertEqual(recommendation_create["module"], "health_model.agent_recommendation_cli")
        self.assertEqual(recommendation_create["command"], "create")
        self.assertEqual(recommendation_create["consumes"], ["agent_readable_daily_context", "recommendation_resolution_window_retrieval_envelope"])
        self.assertEqual(recommendation_create["produces"], ["agent_recommendation_dated", "agent_recommendation_latest"])
        self.assertEqual(
            recommendation_create["payload_shape"]["required_fields"],
            [
                "user_id",
                "date",
                "context_artifact_path",
                "context_artifact_id",
                "resolution_window_artifact_path",
                "recommendation_id",
                "summary",
                "rationale",
                "evidence_refs",
                "confidence_score",
                "policy_basis",
            ],
        )
        self.assertEqual(recommendation_args["payload_json"]["type"], "json_object")
        self.assertFalse(recommendation_args["payload_json"]["required"])
        self.assertFalse(recommendation_args["payload_path"]["required"])

        writeback_judgment = contract["supported_operations"]["writeback.recommendation_judgment"]
        writeback_args = {arg["name"]: arg for arg in writeback_judgment["args"]}
        self.assertEqual(writeback_judgment["module"], "health_model.agent_memory_write_cli")
        self.assertEqual(writeback_judgment["command"], "recommendation-judgment")
        self.assertEqual(writeback_judgment["implementation_status"], "proof_complete")
        self.assertEqual(writeback_judgment["consumes"], ["agent_recommendation"])
        self.assertEqual(writeback_judgment["produces"], ["recommendation_judgment_dated", "recommendation_judgment_latest"])
        self.assertEqual(writeback_judgment["response_envelope"], "writeback")
        self.assertEqual(writeback_args["payload_json"]["type"], "json_object")
        self.assertFalse(writeback_args["payload_json"]["required"])
        self.assertFalse(writeback_args["payload_path"]["required"])

        writeback_transition = contract["supported_operations"]["writeback.recommendation_resolution_transition"]
        writeback_transition_args = {arg["name"]: arg for arg in writeback_transition["args"]}
        self.assertEqual(writeback_transition["module"], "health_model.agent_memory_write_cli")
        self.assertEqual(writeback_transition["command"], "recommendation-resolution-transition")
        self.assertEqual(writeback_transition["implementation_status"], "proof_complete")
        self.assertEqual(
            writeback_transition["consumes"],
            ["agent_recommendation", "recommendation_judgment", "recommendation_resolution_window_memory"],
        )
        self.assertIn("feedback_window_memory_path", writeback_transition["payload_shape"]["optional_fields"])
        self.assertEqual(writeback_transition_args["output_dir"]["flag"], "--output-dir")
        self.assertFalse(writeback_transition_args["payload_json"]["required"])
        self.assertFalse(writeback_transition_args["payload_path"]["required"])
        self.assertEqual(
            writeback_judgment["payload_shape"]["required_fields"],
            [
                "user_id",
                "date",
                "recommendation_artifact_path",
                "recommendation_artifact_id",
                "judgment_id",
                "judgment_label",
                "action_taken",
                "why",
                "written_at",
                "request_id",
                "requested_at",
            ],
        )

        consumed = contract["artifact_types"]["consumed"]
        self.assertEqual(consumed[2]["artifact_type"], "voice_note_submission_payload")
        self.assertIn("--payload-path", consumed[2]["shape"])

        produced = contract["artifact_types"]["produced"]
        self.assertEqual(produced[0]["artifact_type"], "shared_input_bundle")
        self.assertIn("{output_dir}/shared_input_bundle_{date}.json", produced[0]["paths"])
        self.assertEqual(produced[1]["artifact_type"], "agent_readable_daily_context")
        self.assertIn("{output_dir}/agent_readable_daily_context_latest.json", produced[1]["paths"])
        self.assertIn("submit.voice_note", produced[1]["notes"])
        self.assertEqual(produced[2]["artifact_type"], "agent_recommendation")
        self.assertIn("{output_dir}/agent_recommendation_latest.json", produced[2]["paths"])
        self.assertIn("recommendation.create", produced[2]["notes"])
        self.assertIn("policy_basis", produced[2]["notes"])
        self.assertEqual(produced[3]["artifact_type"], "recommendation_judgment")
        self.assertIn("{output_dir}/recommendation_judgment_latest.json", produced[3]["paths"])
        self.assertIn("writeback.recommendation_judgment", produced[3]["notes"])
        self.assertEqual(
            contract["response_envelopes"]["bootstrap.init"]["success_keys"],
            ["ok", "bundle_path", "bundle", "validation", "error"],
        )
        self.assertEqual(
            contract["response_envelopes"]["recommendation.create"]["success_keys"],
            ["ok", "artifact_path", "latest_artifact_path", "recommendation", "validation", "error"],
        )
        self.assertEqual(
            contract["response_envelopes"]["writeback"]["success_keys"],
            ["ok", "artifact_path", "latest_artifact_path", "writeback", "validation", "error"],
        )
        self.assertEqual(
            contract["response_envelopes"]["retrieval"]["success_keys"],
            ["ok", "artifact_path", "retrieval", "validation", "error"],
        )
        self.assertEqual(
            contract["response_envelopes"]["retrieval"]["retrieval_keys"],
            [
                "operation",
                "scope",
                "coverage_status",
                "generated_from",
                "evidence",
                "important_gaps",
                "conflicts",
                "unsupported_claims",
            ],
        )
        self.assertEqual(contract["proof_artifacts"]["human_contract"], "docs/retrieval_contract_v1.md")
        self.assertEqual(contract["proof_artifacts"]["machine_contract"], "artifacts/contracts/retrieval_contract_v1.json")
        self.assertEqual(contract["proof_artifacts"]["memory_write_human_contract"], "docs/memory_write_contract_v1.md")
        self.assertEqual(contract["proof_artifacts"]["memory_write_machine_contract"], "artifacts/contracts/memory_write_contract_v1.json")
        self.assertEqual(
            contract["proof_artifacts"]["weekly_pattern_review_proof_bundle"],
            "artifacts/protocol_layer_proof/2026-04-11-weekly-pattern-review/",
        )
        self.assertEqual(
            contract["proof_artifacts"]["recommendation_retrieval_proof_bundle"],
            "artifacts/protocol_layer_proof/2026-04-11-recommendation-retrieval/",
        )
        self.assertEqual(
            contract["proof_artifacts"]["recommendation_judgment_retrieval_proof_bundle"],
            "artifacts/protocol_layer_proof/2026-04-11-recommendation-judgment-retrieval/",
        )
        self.assertEqual(
            contract["proof_artifacts"]["recommendation_feedback_retrieval_proof_bundle"],
            "artifacts/protocol_layer_proof/2026-04-11-recommendation-feedback/",
        )
        self.assertEqual(
            contract["proof_artifacts"]["recommendation_feedback_window_retrieval_proof_bundle"],
            "artifacts/protocol_layer_proof/2026-04-11-recommendation-feedback-window/",
        )
        self.assertEqual(
            contract["proof_artifacts"]["recommendation_creation_with_resolution_window_grounding_proof_bundle"],
            "artifacts/protocol_layer_proof/2026-04-11-recommendation-creation-with-resolution-window-grounding/",
        )
        self.assertEqual(
            contract["proof_artifacts"]["recommendation_resolution_transition_writeback_proof_bundle"],
            "artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition-writeback/",
        )
        self.assertEqual(
            contract["proof_artifacts"]["contract_describe_writeback_transition_parity_proof_bundle"],
            "artifacts/protocol_layer_proof/2026-04-12-contract-describe-writeback-transition-parity/",
        )

    def test_contract_describe_bootstrap_voice_note_submit_and_context_get_prove_external_agent_loop(self) -> None:
        contract_result = self._run_cli(["describe"])
        submit_voice_note = contract_result["contract"]["supported_operations"]["submit.voice_note"]

        with tempfile.TemporaryDirectory() as temp_dir:
            health_dir = Path(temp_dir) / "data" / "health"
            bundle_path = health_dir / "shared_input_bundle_2026-04-09.json"
            dated_artifact_path = health_dir / "agent_readable_daily_context_2026-04-09.json"

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
            submit = self._run_module(
                submit_voice_note["module"],
                [
                    submit_voice_note["command"],
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
                ],
            )
            context = self._run_module(
                "health_model.agent_context_cli",
                [
                    "get",
                    "--artifact-path",
                    str(dated_artifact_path),
                    "--user-id",
                    "user_dom",
                    "--date",
                    "2026-04-09",
                ],
            )

            self.assertTrue(bootstrap["ok"], msg=bootstrap)
            self.assertTrue(submit["ok"], msg=submit)
            self.assertTrue(context["ok"], msg=context)
            self.assertEqual(submit["bundle_path"], str(bundle_path))
            self.assertEqual(submit["dated_artifact_path"], str(dated_artifact_path))
            self.assertEqual(
                submit["accepted_provenance"],
                {
                    "source_artifact_ids": ["artifact_01JQVOICEINTAKE01"],
                    "input_event_ids": ["event_01JQVOICECAF1", "event_01JQVOICELEGS1"],
                    "subjective_entry_ids": ["subjective_01JQVOICESUBJ01"],
                    "manual_log_entry_ids": [],
                },
            )

            generated_from = context["context"]["generated_from"]
            self.assertIn("artifact_01JQVOICEINTAKE01", generated_from["source_artifact_ids"])
            self.assertIn("event_01JQVOICECAF1", generated_from["input_event_ids"])
            self.assertIn("event_01JQVOICELEGS1", generated_from["input_event_ids"])
            self.assertEqual(generated_from["subjective_entry_ids"], ["subjective_01JQVOICESUBJ01"])

            subjective_signal = next(
                signal
                for signal in context["context"]["explicit_grounding"]["signals"]
                if signal["domain"] == "subjective_state" and signal["signal_key"] == "energy"
            )
            self.assertEqual(subjective_signal["value"], 2)
            self.assertTrue(subjective_signal["evidence_refs"])

    def test_describe_exposes_retrieval_contract_metadata_and_expected_operations_fixture(self) -> None:
        result = self._run_cli(["describe"])
        expected = json.loads((RETRIEVAL_FIXTURE_DIR / "retrieval_contract_v1_expected_operations.json").read_text())

        self.assertEqual(result["contract"]["accepted_enums"]["retrieval_operations"], expected["operations"])

        day_context = result["contract"]["supported_operations"]["retrieve.day_context"]
        self.assertEqual(day_context["module"], "health_model.agent_context_cli")
        self.assertEqual(day_context["command"], "get")
        self.assertEqual(day_context["mode"], "read")

        day_nutrition_brief = result["contract"]["supported_operations"]["retrieve.day_nutrition_brief"]
        self.assertEqual(day_nutrition_brief["module"], "health_model.day_nutrition_brief")
        self.assertEqual(day_nutrition_brief["command"], "retrieve-day-nutrition-brief")
        self.assertEqual(day_nutrition_brief["implementation_status"], "proof_complete")
        self.assertEqual(day_nutrition_brief["consumes"], ["day_nutrition_brief"])
        self.assertEqual(day_nutrition_brief["response_envelope"], "retrieval")

        sleep_review = result["contract"]["supported_operations"]["retrieve.sleep_review"]
        self.assertEqual(sleep_review["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(sleep_review["command"], "sleep-review")
        self.assertEqual(sleep_review["implementation_status"], "proof_complete")

        recommendation = result["contract"]["supported_operations"]["retrieve.recommendation"]
        self.assertEqual(recommendation["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation["command"], "recommendation")
        self.assertEqual(recommendation["implementation_status"], "proof_complete")

        recommendation_judgment = result["contract"]["supported_operations"]["retrieve.recommendation_judgment"]
        self.assertEqual(recommendation_judgment["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation_judgment["command"], "recommendation-judgment")
        self.assertEqual(recommendation_judgment["implementation_status"], "proof_complete")

        recommendation_feedback = result["contract"]["supported_operations"]["retrieve.recommendation_feedback"]
        self.assertEqual(recommendation_feedback["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation_feedback["command"], "recommendation-feedback")
        self.assertEqual(recommendation_feedback["implementation_status"], "proof_complete")

        recommendation_feedback_window = result["contract"]["supported_operations"]["retrieve.recommendation_feedback_window"]
        self.assertEqual(recommendation_feedback_window["module"], "health_model.agent_retrieval_cli")
        self.assertEqual(recommendation_feedback_window["command"], "recommendation-feedback-window")
        self.assertEqual(recommendation_feedback_window["implementation_status"], "proof_complete")

        weekly_review = result["contract"]["supported_operations"]["retrieve.weekly_pattern_review"]
        self.assertEqual(weekly_review["module"], "health_model.agent_context_cli")
        self.assertEqual(weekly_review["command"], "retrieve-weekly-pattern-review")
        self.assertEqual(weekly_review["implementation_status"], "proof_complete")

    def test_retrieve_day_context_contract_matches_current_repo_reality_and_fixture_shape(self) -> None:
        result = self._run_cli(["describe"])
        request_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "day_context_smoke_request.json").read_text())
        response_fixture = json.loads((RETRIEVAL_FIXTURE_DIR / "day_context_smoke_response.json").read_text())
        artifact_path = REPO_ROOT / request_fixture["artifact_path"]

        context = self._run_module(
            "health_model.agent_context_cli",
            [
                "get",
                "--artifact-path",
                str(artifact_path),
                "--user-id",
                request_fixture["user_id"],
                "--date",
                request_fixture["date"],
            ],
        )

        retrieval = {
            "ok": context["ok"],
            "artifact_path": request_fixture["artifact_path"],
            "retrieval": {
                "operation": "retrieve.day_context",
                "scope": {
                    "user_id": request_fixture["user_id"],
                    "date": request_fixture["date"],
                },
                "coverage_status": "partial" if context["context"]["important_gaps"] else "present",
                "generated_from": context["context"]["generated_from"],
                "evidence": "agent_readable_daily_context",
                "important_gaps": [gap["code"] for gap in context["context"]["important_gaps"]],
                "conflicts": context["context"]["conflicts"],
                "unsupported_claims": [],
            },
            "validation": {
                "is_valid": True,
                "schema_issues": [],
                "semantic_issues": [],
                "request_echo": {
                    "request_id": request_fixture["request_id"],
                    "requested_at": request_fixture["requested_at"],
                },
            },
            "error": None,
        }

        self.assertTrue(context["ok"], msg=context)
        self.assertEqual(result["contract"]["response_envelopes"]["retrieval"]["retrieval_keys"], list(retrieval["retrieval"].keys()))
        self.assertEqual(retrieval, response_fixture)

    def test_retrieve_day_context_fails_closed_on_wrong_scope(self) -> None:
        artifact_path = REPO_ROOT / "data" / "health" / "agent_readable_daily_context_2026-04-10.json"

        wrong_user = self._run_module(
            "health_model.agent_context_cli",
            [
                "get",
                "--artifact-path",
                str(artifact_path),
                "--user-id",
                "user_other",
                "--date",
                "2026-04-10",
            ],
            expected_returncode=1,
        )
        wrong_date = self._run_module(
            "health_model.agent_context_cli",
            [
                "get",
                "--artifact-path",
                str(artifact_path),
                "--user-id",
                "user_dom",
                "--date",
                "2026-04-09",
            ],
            expected_returncode=1,
        )

        self.assertFalse(wrong_user["ok"])
        self.assertEqual(wrong_user["error"]["code"], "artifact_user_mismatch")
        self.assertFalse(wrong_date["ok"])
        self.assertEqual(wrong_date["error"]["code"], "artifact_date_mismatch")

    def test_invalid_command_returns_fail_closed_json_error_shape(self) -> None:
        result = self._run_cli(["nope"], expected_returncode=1)

        self.assertFalse(result["ok"])
        self.assertIsNone(result["contract"])
        self.assertFalse(result["validation"]["is_valid"])
        self.assertEqual(result["error"]["code"], "cli_parse_error")
        self.assertIn("invalid choice", result["error"]["message"])
        self.assertEqual(sorted(result.keys()), ["contract", "error", "ok", "validation"])

    def _run_cli(self, args: list[str], *, expected_returncode: int = 0) -> dict[str, object]:
        return self._run_module("health_model.agent_contract_cli", args, expected_returncode=expected_returncode)

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
