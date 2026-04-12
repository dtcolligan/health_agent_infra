from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_canonical_public_demo.py"
EXPECTED_MODULES = {
    "health_agent_infra.agent_contract_cli",
    "health_agent_infra.agent_bundle_cli",
    "health_agent_infra.agent_voice_note_cli",
    "health_agent_infra.agent_context_cli",
    "health_agent_infra.agent_recommendation_cli",
}


class RunCanonicalPublicDemoWrapperTest(unittest.TestCase):
    def test_wrapper_uses_canonical_health_agent_infra_modules_only(self) -> None:
        script_text = SCRIPT_PATH.read_text()

        self.assertNotIn("health_model.", script_text)
        for module_name in EXPECTED_MODULES:
            self.assertIn(module_name, script_text)


if __name__ == "__main__":
    unittest.main()
