"""Legacy pre-rebuild demo shim.

This script is retained only so archived pre-rebuild proof artifacts can
still be replayed. The module names it references are historical and do
not describe the shipped v1 runtime surfaces.
"""

from __future__ import annotations

import runpy
from pathlib import Path

CANONICAL_MODULES = (
    "health_model.agent_contract_cli",
    "health_model.agent_bundle_cli",
    "health_model.agent_voice_note_cli",
    "health_model.agent_context_cli",
    "health_model.agent_recommendation_cli",
)

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "reporting" / "scripts" / "run_canonical_public_demo.py"

def main() -> None:
    runpy.run_path(str(SCRIPT_PATH), run_name="__main__")

if __name__ == "__main__":
    main()
