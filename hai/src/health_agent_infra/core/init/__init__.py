"""W-AA (v0.1.13) — first-time-user `hai init --guided` onboarding flow.

The non-guided `hai init` (in `cli.py:cmd_init`) stays a non-interactive
3-step setup (thresholds + state DB + skills). The `--guided` flag adds
four further steps that prompt a real user through the data the runtime
needs before it can plan a day:

    4. Intervals.icu credential prompt (skip if present).
    5. Initial intent + target authoring (skip if active rows present).
    6. First wellness pull (skip if today's row already projected).
    7. Surface `hai today` so the user sees the cold-start prose.

Each step is naturally idempotent — a `KeyboardInterrupt` mid-prompt
leaves the state DB unchanged, and re-running `hai init --guided`
resumes at the first incomplete step.

Note that this module owns *orchestration*, not coaching prose. The
prompts ask for facts (kcal target, training focus); they don't dispense
recommendations. The skills + agent loop still own coaching.
"""

from health_agent_infra.core.init.onboarding import (
    OnboardingResult,
    PromptInterface,
    StdinPrompts,
    ScriptedPrompts,
    run_guided_onboarding,
)

__all__ = [
    "OnboardingResult",
    "PromptInterface",
    "StdinPrompts",
    "ScriptedPrompts",
    "run_guided_onboarding",
]
