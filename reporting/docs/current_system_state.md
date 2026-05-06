# Current system state

**Status:** current truth as of v0.1.17 ship on 2026-05-05.

This file is the short operational answer to "what is true now?"
Use it before reading cycle-level audit history. Release artifacts
(`PLAN.md`, `RELEASE_PROOF.md`, `REPORT.md`, Codex responses) remain
the provenance trail; this file is the current-state map.

## Shipped baseline

| Surface | Current value | Source of truth |
|---|---|---|
| Package version | `0.1.17` | `pyproject.toml`, `CHANGELOG.md` |
| Published posture | Shipped to PyPI 2026-05-05; v0.1.18 (onboarding-quality cycle) is next-active | `reporting/plans/v0_1_17/RELEASE_PROOF.md`, [PyPI](https://pypi.org/project/health-agent-infra/) |
| Schema head | `26` (W-B `body_comp` added v0.1.17) | `src/health_agent_infra/core/state/migrations/` |
| CLI commands | 67 annotated `hai` commands (v0.1.15 baseline 60 + `hai sync purge` + `hai intake weight` + `hai eval review {list,show,tag,dismiss,export}`) | `hai capabilities --json` |
| CLI source layout | `cli/__init__.py` (~2986 LOC parser-tree builder + dispatch) + `cli/handlers/{auth,pull_clean,state,config_init,intake,intent,target,recommend,review,inspect,tools}.py` (each <2500 LOC). W-29 mechanical split landed v0.1.17. | `src/health_agent_infra/cli/` |
| Test gate at release | 2683 passed, 4 skipped (full suite); `hai eval run --scenario-set all` 135/135 PASS; persona matrix 13/13 with 0 findings + 0 crashes (opt-in via `HAI_RUN_PERSONA_MATRIX=1`) | `reporting/plans/v0_1_17/RELEASE_PROOF.md` |
| Eval scenario corpus | 135 deterministic fixtures (20 per domain × 6 + 15 synthesis) + 30 judge_adversarial fixtures | `src/health_agent_infra/evals/scenarios/` |
| Domains | recovery, running, sleep, stress, strength, nutrition | `src/health_agent_infra/domains/` |
| Runtime state | local SQLite by default; no package telemetry | `reporting/docs/privacy.md`, `SECURITY.md` |

## Product claim

Health Agent Infra is the local plugin/runtime wrapper around a
shell-capable personal-health agent. The maintainer dogfoods it daily.
v0.1.15 made the package installable from PyPI for a non-maintainer
and closed the candidate package bugs found before publish. v0.1.15.1
repaired Linux keyring fall-through. v0.1.17 consolidated the
maintainability + eval-substrate carry-over (W-29 cli.py split,
W-AH-2 scenario corpus, W-B body-comp intake, W-D arm-2 partial-day
projection).

The stronger claim, "a non-maintainer completed the full flow under
recorded observation," is **not yet proven**. v0.1.16 was scoped as
the empirical post-publish cycle but cancelled 2026-05-04 when its
named candidate became unavailable; the empirical work was renumbered
to v0.1.19 and a new v0.1.18 onboarding-quality cycle inserted before
it to close known onboarding gaps proactively. v0.1.19 will run the
foreign-user session against the post-v0.1.18 PyPI build.

## v0.1.17 shipped

- W-29: `cli.py` 9,927 LOC mechanical split into 1 main + 1 shared
  module + 11 handler-group modules under
  `src/health_agent_infra/cli/handlers/` (each <2,500 LOC); manifest
  byte-stable; new `test_cli_handler_dispatch_smoke.py` +
  `test_cli_handler_group_loc_ceiling.py` regression contracts.
- W-30: capabilities-manifest schema regression test
  (`test_capabilities_manifest_schema.py`) — pins field names and
  types, not values. Schema freeze itself remains v0.2.3.
- W-AH-2: scenario fixture corpus 35 → 135 across six domains
  (20 each) + synthesis (15); 100% pass-rate.
- W-AI-2: `hai eval review` CLI surface (list/show/tag/dismiss/export)
  with per-user triage state at `~/.local/share/health_agent_infra/eval_review.json`.
- W-AM-2: 4 escalate-tagged adversarial scenarios (sleep/strength/
  stress/nutrition); cumulative 6/6.
- W-Vb-4: 12-of-12 P1..P12 persona closure + P13 matrix-only
  (0 findings, 0 crashes); opt-in regression test pins the contract.
- W-B: `hai intake weight` body-composition surface + `body_comp`
  table + migration 026; user-authored only.
- W-D arm-2: partial-day end-of-day macro projection (target-anchored
  default; linear-extrapolation reachable via threshold override).
- W-C-EQP: migration 025 query-plan stability assertion.
- F-PV14-02: `hai sync purge` surgical-cleanup CLI; refuses selectors
  matching >5 rows; writes `runtime_event_log` audit row.

## v0.1.15 / v0.1.15.1 shipped

- `gym_set.set_id` now includes exercise slug; migration 024 rewrites
  old-format ids while preserving custom correction rows.
- CSV fixtures default-deny against the canonical state DB on both
  `hai pull` and `hai daily`; explicit opt-in or demo/non-canonical
  destination required.
- `hai intake gaps` emits a `present` block, `is_partial_day`, and
  `target_status` for nutrition target availability.
- `hai target nutrition` writes four atomic macro target rows;
  migration 025 extends `target_type` with `carbs_g` and `fat_g`.
- Nutrition classification suppresses partial-day/no-target cases to
  `nutrition_status='insufficient_data'`.
- `merge-human-inputs` consumes the W-A presence block for recap vs
  forward-march framing.
- v0.1.15.1 adds `keyrings.alt` and a defensive `_default_backend()`
  probe so Linux installs without a registered keyring backend degrade
  to env-var/no-credential mode instead of crashing setup/status
  commands.

## Next cycles

| Cycle | Role |
|---|---|
| v0.1.18 | Onboarding-quality cycle (next-active). README pivot to `hai init --guided`, default-flip `hai init` to guided when stdin is a TTY and `onboarding_readiness` reports missing fields, prompt content review, self-onboard dogfood pass, `hai doctor onboarding_readiness` actionability. PLAN.md authors when cycle opens. |
| v0.1.19 | Foreign-user empirical (renumbered from v0.1.16; the originally-scoped post-publish empirical cycle). PLAN.md authors after a recorded foreign-user session against the post-v0.1.18 PyPI build. |
| v0.2.0 | Weekly review (W52) + deterministic factuality (W58D) + Path A doc adjuncts. Hard deps are v0.1.19 + v0.1.14 substrate, not v0.1.17/v0.1.18 — parallelizable. |

## How to update this file

Update this file after any release that changes package version,
schema head, command count, test gate, product claim, or next-cycle
role. Do not mirror detailed CLI command metadata here; regenerate
`reporting/docs/agent_cli_contract.md` from
`hai capabilities --markdown` instead.
