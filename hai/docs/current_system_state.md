# Current system state

**Status:** current truth as of the v0.2.0 source tree and
runtime-contract research reframe on 2026-05-07.

This file is the short operational answer to "what is true now?"
Use it before reading cycle-level audit history. Release artifacts
(`PLAN.md`, `RELEASE_PROOF.md`, `REPORT.md`, Codex responses) remain
the provenance trail; this file is the current-state map.

## Repo-level frame

The repo is now a runtime-contract research repo with three active
artifacts:

- **Runtime contract** — capabilities manifest, typed commands,
  mutation classes, `agent_safe`, schemas, proposal/commit separation,
  deterministic gates, policy, and audit.
- **HAI** — personal-wellness reference runtime packaged as
  `health-agent-infra`.
- **GovernedAgentBench** — benchmark scaffold for measuring
  contract-governed agent operation.

Current priority is the merged NeurIPS 2027 paper, GovernedAgentBench,
and paper-critical HAI contract work. HAI v1 polish is subordinate
unless it supports those artifacts. Canonical sources:
[`../../project/FRAME.md`](../../project/FRAME.md),
[`../../project/DECISIONS.md`](../../project/DECISIONS.md),
[`../../project/OPERATING_MODEL.md`](../../project/OPERATING_MODEL.md),
[`../../research/runtime_contracts_paper/framing_v2/CONVERGED.md`](../../research/runtime_contracts_paper/framing_v2/CONVERGED.md),
[`../../research/runtime_contracts_paper/PAPER_FRAME.md`](../../research/runtime_contracts_paper/PAPER_FRAME.md),
[`../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md),
and
[`../../benchmark/governed_agent_bench/README.md`](../../benchmark/governed_agent_bench/README.md).

## Research-lane status

| Surface | Current value | Source of truth |
|---|---|---|
| Paper frame | Locked title (*Deterministic Software Contracts as Trusted Monitors in AI Control Protocols*), NeurIPS 2027 main-conference target, contribution list, empirical result tiers, and non-clinical boundary are locked as framing. | `research/runtime_contracts_paper/framing_v2/CONVERGED.md`, `research/runtime_contracts_paper/PAPER_FRAME.md` |
| Paper draft | Live skeleton exists; empirical sections remain placeholders until benchmark tasks, baselines, fine-tuning, and ablations run. | `research/runtime_contracts_paper/superseded/DRAFT_PAPER.md` |
| Evaluation strategy | Local, cloud, fine-tuned, rule, and scaffold-ablation conditions are in scope; deterministic safety metrics are primary. | `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` |
| GovernedAgentBench | Scaffold only: 0 frozen manifests, 0 pilot tasks, 0 recorded trajectories, no scorer implementation, no baselines, no reports. | `benchmark/governed_agent_bench/README.md` |
| Experiments | Not run yet. Next step is GovernedAgentBench measurement-readiness before model backends. | `project/ROADMAP.md`, `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md` |

## Shipped baseline

| Surface | Current value | Source of truth |
|---|---|---|
| Source package version | `0.2.0` | `pyproject.toml`, `CHANGELOG.md` |
| Published posture | Source tree is at v0.2.0 after D15 IR round 3 `SHIP`; PyPI availability is external and should be checked separately when publishing or installing. | `hai/reporting/plans/v0_2_0/codex_implementation_review_round_3_response.md`, [PyPI](https://pypi.org/project/health-agent-infra/) |
| Schema head | `28` (v0.2.0 W-EVCARD-DAILY migration 027 + W-EVCARD-WEEKLY migration 028; was 26 at v0.1.18 close) | `hai/src/health_agent_infra/core/state/migrations/` |
| CLI commands | 68 annotated `hai` commands (v0.2.0 adds `hai review weekly`; v0.1.17/v0.1.18 baseline was 67). New `hai review weekly` flags: `--week`, `--json`/`--markdown`, `--user-id`, `--coverage-threshold`, `--include-history`, `--db-path`, `--bypass-factuality-gate`. New `--scenario-set factuality` choice on `hai eval run`. | `hai capabilities --json` |
| CLI source layout | `cli/__init__.py` (~3200 LOC parser-tree builder + dispatch) + `cli/handlers/{auth,pull_clean,state,config_init,intake,intent,target,recommend,review,inspect,tools}.py` (each <2500 LOC). W-29 mechanical split landed v0.1.17. | `hai/src/health_agent_infra/cli/` |
| Test gate at release | 2943 passed, 4 skipped (full suite, broader `-W error::Warning` gate, ~140s; +187 vs v0.1.18 baseline of 2756, exceeded the +86 PLAN G2 floor 2.2×; +3 over the Phase-3 close 2940 baseline are the IR R1 regression tests for F-IR-01 + F-IR-05); `hai eval run --scenario-set all` 100% across deterministic + factuality fan-out; `hai eval run --scenario-set factuality` 100/100 vs 97/99 thresholds; persona matrix 13/13 with 0 findings + 0 crashes (opt-in via `HAI_RUN_PERSONA_MATRIX=1`) | `hai/reporting/plans/v0_2_0/RELEASE_PROOF.md` |
| Eval scenario corpus | 135 deterministic fixtures (20 per domain × 6 + 15 synthesis) + 30 judge_adversarial fixtures + 30 atomic_claims fixtures (W-FACT-ATOM corpus) + 160 factuality fixtures (W58D corpus, 85 known-bad + 75 known-good) | `hai/src/health_agent_infra/evals/scenarios/` |
| Domains | recovery, running, sleep, stress, strength, nutrition | `hai/src/health_agent_infra/domains/` |
| Runtime state | local SQLite by default; no package telemetry | `hai/docs/privacy.md`, `SECURITY.md` |

## HAI reference-runtime claim

Health Agent Infra is the local plugin/runtime wrapper around a
shell-capable personal-health agent. The maintainer dogfoods it daily.
v0.1.15 made the package installable from PyPI for a non-maintainer
and closed the candidate package bugs found before publish. v0.1.15.1
repaired Linux keyring fall-through. v0.1.17 consolidated the
maintainability + eval-substrate carry-over (W-29 cli.py split,
W-AH-2 scenario corpus, W-B body-comp intake, W-D arm-2 partial-day
projection). v0.1.18 closed the onboarding ergonomics + upgrade-path
correctness work (W-OB-2 `hai init` interactive default, W-OB-7
intake-handler migration parity closing F-OB-PRE-01, W-OB-5
`hai doctor next_action` schema).

The stronger claim, "a non-maintainer completed the full flow with
wearable signal under recorded observation," is **not yet proven**.
v0.1.16 was scoped as the empirical post-publish cycle but cancelled
2026-05-04 when its named candidate became unavailable. v0.1.19
(renumbered empirical scope) was then cancelled 2026-05-06 per
CP-2U-GATE-SPLIT when the candidate-supply criteria proved too narrow
on the v0.2.0 timeline. AGENTS.md D16 splits the original W-2U-GATE
into three claims: **W-2U-INSTALL closed verbal-only** by the
post-v0.1.18 maintainer's-father session; **W-2U-WEARABLE** (full
pipeline with wearable signal) and **W-2U-DOGFOOD** (≥7d daily
non-maintainer use) deferred to v0.4 review.

## v0.2.0 shipped in source tree

- W-PROV-2: locator emission across five dormant domains.
- W-EVCARD-DAILY: `recommendation_evidence_card` table, one card per
  committed recommendation.
- W-EVCARD-WEEKLY: append-only `weekly_claim_card` carrier.
- W52: `hai review weekly` aggregation surface.
- W-FACT-ATOM: deterministic atomic-claim parser.
- W58D: deterministic factuality gate over quantitative and comparative
  weekly-review claims.
- W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD, W-EXPLAIN-UX-CARRY:
  doc and carry-forward adjuncts.
- D15 IR round 3 verdict: `SHIP`.

## v0.1.18 shipped

- W-OB-1: README quickstart pivot to bare `hai init` as the primary
  first-run command (post-W-OB-2 default-flip shape; W-OB-2 auto-
  promotion documented inline + opt-outs enumerated; `--guided`
  retained as explicit-force spelling). `agent_integration.md:27`
  install lead matches. Pure docs.
- W-OB-2: `hai init` interactive default. When stdin is a TTY AND
  `check_onboarding_readiness` reports incomplete state, bare
  `hai init` auto-promotes to the `--guided` flow. Opt-outs:
  `--non-interactive` flag + `HAI_INIT_NON_INTERACTIVE=1` env var.
  5-case test surface; manifest snapshot regenerated for the new flag.
- W-OB-3: `--guided` prompt content review. Content-only
  `next_action_hint` field on `OnboardingResult` (points user at
  `hai daily` post-onboarding, with remediation if creds/intent skipped).
  Empty-input affordance tests (no literal `skip` keyword).
- W-OB-4a: Phase 1 upgrade-from-old-DB dogfood. W-OB-7 fix verified
  end-to-end against synthetic schema-25 DB.
- W-OB-4b: Phase 2 post-W-OB-2 local-wheel smoke. Both opt-out paths
  verified end-to-end. TTY default-flip UX confirmation deferred to
  maintainer ship-time manual gate.
- W-OB-5: `hai doctor next_action` field across 9 hint-emitting paths
  (`onboarding_readiness`, `state_db` ×2, `auth_intervals_icu` no-creds
  + deep-probe CAUSE_2_CREDS + NETWORK, `auth_garmin`, `skills` ×2,
  `check_config` ×2, `check_sources`, `check_today` ×2,
  `check_intake_gaps` ×2). Structured shape:
  `{command, purpose, agent_safe, interactive}`. `_NEXT_ACTION_REGISTRY`
  has 11 commands; manifest-consistency invariant pinned by regression
  test. Multi-missing onboarding case prefers umbrella `hai init`.
  CAUSE_1_CLOUDFLARE_UA + OTHER deep-probe outcomes intentionally
  prose-only (diagnostic, no concrete command).
- W-OB-6: conditional absorption slot did NOT fire. No W-OB-6-class
  structural findings.
- W-OB-7: intake-handler migration parity. New
  `open_connection_with_migrations` helper in `core/state/store.py`;
  all 8 `cmd_intake_*` handlers route through it. F-OB-PRE-01
  (intake crash on schema-behind DB) closed end-to-end.

## v0.1.17 shipped

- W-29: `cli.py` 9,927 LOC mechanical split into 1 main + 1 shared
  module + 11 handler-group modules under
  `hai/src/health_agent_infra/cli/handlers/` (each <2,500 LOC); manifest
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
| ~~v0.1.19~~ | **CANCELLED 2026-05-06** per CP-2U-GATE-SPLIT (`hai/reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`) + AGENTS.md D16. Foreign-user empirical scope re-tiered to opportunistic-not-blocking; W-2U-INSTALL closed (verbal-only) by post-v0.1.18 father session; W-2U-WEARABLE + W-2U-DOGFOOD deferred to v0.4 review. |
| Phase 2 doc alignment | **Current research-support cycle.** Align docs to the locked framing in `framing_v2/CONVERGED.md` for the merged NeurIPS 2027 paper; no HAI runtime state changes. |
| GovernedAgentBench measurement-readiness | **Research priority.** Create a benchmark for the merged paper that can evaluate governed agent operation and prove it can score known-good and known-bad trajectories. |
| HAI paper-readiness engineering | **Research priority.** Make HAI usable by the paper and benchmark through public contracts, synthetic fixtures, stable read surfaces, and reproducible baselines. |
| ~~v0.2.1 HAI insight ledger~~ | **Superseded by D-PROJ-016.** HAI is frozen as a product; revive only if selected through a paper- or benchmark-critical runtime-fix packet. |

## How to update this file

Update this file after any release that changes package version,
schema head, command count, test gate, product claim, or next-cycle
role. Do not mirror detailed CLI command metadata here; regenerate
`hai/docs/agent_cli_contract.md` from
`hai capabilities --markdown` instead.
