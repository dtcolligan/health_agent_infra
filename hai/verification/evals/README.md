# Evaluation framework — v1

The eval framework ships **inside the package** at
`src/health_agent_infra/evals/` (runner + CLI + scenarios + rubrics). A
wheel install of `health_agent_infra` therefore carries the full eval
surface, and `hai eval run` works from any working directory without
requiring a repo checkout.

This directory retains only the dev-reference docs:

- `README.md` — this file.
- `skill_harness_blocker.md` — the status record for the partially resolved
  skill-narration axis.

## Where everything now lives

    src/health_agent_infra/evals/
        __init__.py
        runner.py            # scenario loader + scorer
        cli.py               # `hai eval run` argparse entry point
        scenarios/
            recovery/        # domain scenarios
            running/
            sleep/
            stress/
            strength/
            nutrition/
            synthesis/       # X-rule + run_synthesis scenarios
        rubrics/
            domain.md
            synthesis.md

## What this evaluates

- **Domain layer** — `classify.py` + `policy.py` per domain. Scored
  against expected classified bands, forced actions, capped
  confidences, and rule-id firings.
- **Synthesis layer** — `core/synthesis.py` + `core/synthesis_policy.py`.
  Scored against expected X-rule firings (by rule id), final per-domain
  actions, final confidences, and any authored validation-error or
  synthesis-error invariants.

## What packaged `hai eval` deliberately does NOT evaluate

- **Skill narration quality.** Rationale prose, uncertainty prose,
  joint-narration conflict resolution, and any other behaviour that
  lives inside `skills/<name>/SKILL.md` sits outside the packaged
  deterministic runner. Partial coverage exists in repo-local harnesses:
  `verification/evals/skill_harness/` covers recovery + running readiness
  replay/live paths, and `verification/evals/synthesis_harness/` scores
  synthesis-skill output fixtures. Live capture, broader domain coverage, and
  LLM-as-judge scoring remain open.

- **Live pull adapters.** Evals run on frozen evidence bundles; pull paths
  are covered by focused tests such as `test_pull_intervals_icu.py` and
  `test_pull_garmin_live.py` with mocked clients.

See `skill_harness_blocker.md` for the remaining skill-harness work.

## CLI

    hai eval run --domain recovery          # run all recovery scenarios
    hai eval run --synthesis                # run all synthesis scenarios
    hai eval run --domain recovery --json   # machine-readable output

Exit code is 0 when all loaded scenarios pass, 1 when any fails, 2 on
usage error. The command is registered unconditionally on every install
of the package.
