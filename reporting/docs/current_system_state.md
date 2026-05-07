# Current system state

**Status:** current truth as of v0.2.0 Phase-3 close on 2026-05-07
(Phase 5 ship-prep complete; D15 IR + maintainer manual TTY ship
gate pending).

This file is the short operational answer to "what is true now?"
Use it before reading cycle-level audit history. Release artifacts
(`PLAN.md`, `RELEASE_PROOF.md`, `REPORT.md`, Codex responses) remain
the provenance trail; this file is the current-state map.

## Shipped baseline

| Surface | Current value | Source of truth |
|---|---|---|
| Package version | `0.1.18` (v0.2.0 ship-prep complete; version bump + tag at maintainer manual TTY gate) | `pyproject.toml`, `CHANGELOG.md` |
| Published posture | v0.2.0 ship-prep complete 2026-05-07; D15 IR pending; PyPI publish remaining gated on D15 IR settle + maintainer manual TTY ship gate per `reporting/plans/v0_2_0/RELEASE_PROOF.md` §8. **v0.2.1 (insight ledger — W53) is next-active post-v0.2.0 ship.** | `reporting/plans/v0_2_0/RELEASE_PROOF.md`, [PyPI](https://pypi.org/project/health-agent-infra/) |
| Schema head | `28` (v0.2.0 W-EVCARD-DAILY migration 027 + W-EVCARD-WEEKLY migration 028; was 26 at v0.1.18 close) | `src/health_agent_infra/core/state/migrations/` |
| CLI commands | 68 annotated `hai` commands (v0.2.0 adds `hai review weekly`; v0.1.17/v0.1.18 baseline was 67). New `hai review weekly` flags: `--week`, `--json`/`--markdown`, `--user-id`, `--coverage-threshold`, `--include-history`, `--db-path`, `--bypass-factuality-gate`. New `--scenario-set factuality` choice on `hai eval run`. | `hai capabilities --json` |
| CLI source layout | `cli/__init__.py` (~3200 LOC parser-tree builder + dispatch) + `cli/handlers/{auth,pull_clean,state,config_init,intake,intent,target,recommend,review,inspect,tools}.py` (each <2500 LOC). W-29 mechanical split landed v0.1.17. | `src/health_agent_infra/cli/` |
| Test gate at release | 2940 passed, 4 skipped (full suite, broader `-W error::Warning` gate, ~140s; +184 vs v0.1.18 baseline of 2756, exceeded the +86 PLAN G2 floor 2.1×); `hai eval run --scenario-set all` 100% across deterministic + factuality fan-out; `hai eval run --scenario-set factuality` 100/100 vs 97/99 thresholds; persona matrix 13/13 with 0 findings + 0 crashes (opt-in via `HAI_RUN_PERSONA_MATRIX=1`) | `reporting/plans/v0_2_0/RELEASE_PROOF.md` |
| Eval scenario corpus | 135 deterministic fixtures (20 per domain × 6 + 15 synthesis) + 30 judge_adversarial fixtures + 30 atomic_claims fixtures (W-FACT-ATOM corpus) + 160 factuality fixtures (W58D corpus, 85 known-bad + 75 known-good) | `src/health_agent_infra/evals/scenarios/` |
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

## v0.1.18 shipped (D15 IR closed at R3; PyPI publish gated only on maintainer manual TTY ship gate)

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
| ~~v0.1.19~~ | **CANCELLED 2026-05-06** per CP-2U-GATE-SPLIT (`reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`) + AGENTS.md D16. Foreign-user empirical scope re-tiered to opportunistic-not-blocking; W-2U-INSTALL closed (verbal-only) by post-v0.1.18 father session; W-2U-WEARABLE + W-2U-DOGFOOD deferred to v0.4 review. |
| v0.2.0 | **Ship-prep complete 2026-05-07.** Weekly review (W52) + deterministic factuality (W58D) + W-PROV-2 dormant-domain locators + W-EVCARD-DAILY (migration 027) + W-EVCARD-WEEKLY (migration 028) + W-FACT-ATOM corpus + Path A doc adjuncts (W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD) + W-EXPLAIN-UX-CARRY disposition tracker. D15 IR in flight; PyPI publish gated on IR settle + maintainer manual TTY gate per `reporting/plans/v0_2_0/RELEASE_PROOF.md` §8. **Foreign-user empirical evidence re-tiered to opportunistic-not-blocking per D16.** |
| v0.2.1 | **Next-active post-v0.2.0 ship.** Insight ledger (W53) + carry-over from v0.2.0 IR if any findings flag-deferred. |

## How to update this file

Update this file after any release that changes package version,
schema head, command count, test gate, product claim, or next-cycle
role. Do not mirror detailed CLI command metadata here; regenerate
`reporting/docs/agent_cli_contract.md` from
`hai capabilities --markdown` instead.
