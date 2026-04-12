from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_canonical_public_demo.py"
EXPECTED_CANONICAL_MODULES = {
    "health_model.agent_contract_cli",
    "health_model.agent_bundle_cli",
    "health_model.agent_voice_note_cli",
    "health_model.agent_context_cli",
    "health_model.agent_recommendation_cli",
}

EXPECTED_COMPAT_MODULES = {
    "health_agent_infra.agent_contract_cli",
    "health_agent_infra.agent_bundle_cli",
    "health_agent_infra.agent_voice_note_cli",
    "health_agent_infra.agent_context_cli",
    "health_agent_infra.agent_recommendation_cli",
}


class RunCanonicalPublicDemoWrapperTest(unittest.TestCase):
    def test_wrapper_uses_canonical_health_model_modules(self) -> None:
        script_text = SCRIPT_PATH.read_text()

        for module_name in EXPECTED_CANONICAL_MODULES:
            self.assertIn(module_name, script_text)

    def test_wrapper_no_longer_teaches_compat_namespace_as_canonical(self) -> None:
        script_text = SCRIPT_PATH.read_text()

        for module_name in EXPECTED_COMPAT_MODULES:
            self.assertNotIn(module_name, script_text)


if __name__ == "__main__":
    unittest.main()
