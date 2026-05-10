# Mechanism Inventory

**Status:** Phase 1 audit deliverable, WP-INV-001 completed against
source on 2026-05-10.

This file is the operational record of where each runtime mechanism
lives in HAI source and whether the off-path is cleanly isolatable.
Phase 1 (`WP-INV-001`) has verified the previously provisional
placements against HAI source. The records below are source-backed
and should be treated as the gateway input for Phase 2 runtime-mode,
refusal, and dispatch work.

The audit is the gateway artifact for the runtime-first paper plan.
Phase 2 (`WP-RT-MODE-*`, `WP-REFUSE-*`, `WP-DISPATCH-*`) cannot
proceed cleanly until the seams in this file are real, not
hypothetical.

## Round-2 changes from round 1

- **M5 (`agent_safe`) and M6 (`proposal_gate`) stay separate.** Per
  D-PROJ-017 (b), Phase 2 builds a real CLI-dispatch-level
  `agent_safe` enforcer (`WP-DISPATCH-001`) so the two mechanisms
  become independently ablatable. Today they are functionally
  entangled in the W57 user-gate; their separation is a Phase 2
  engineering deliverable, not a current code property.
- **M7 (refusal) build path locked.** Per D-PROJ-017 (c), Phase 2
  builds a centralized `core/refusal/` runtime seam. Existing
  per-domain validators in `core/validate.py` and
  `core/writeback/proposal.py` may inform the design but the
  deliverable is a fresh canonical surface, not an incremental
  augmentation of skills.
- **M8 (audit_chain) narrowed.** Per D-PROJ-017 (d), the ablatable
  scope is evidence-reference emission only. Atomic state-graph
  writes are a non-ablatable invariant called M9-TX.
- **M9-TX added as held-constant.** Transaction integrity is treated
  as a fundamental safety property, always on. Disabling it would
  corrupt the system rather than measure anything; never made
  ablatable.
- **`no_runtime_enforcement` instead of `no_runtime`.** Per
  D-PROJ-017 (f). The held-constant harness controls (M1-M3) stay
  on even in this mode.
- **HAI hermeticity surface uses the real env vars.** Per
  F-CDX-RFR-R1-11: HAI_STATE_DB, HAI_BASE_DIR, the demo session
  marker, and platform config paths. There is no `HAI_STATE_PATH`
  today; the round-1 plan invented one. WP-HRN-002 reframes around
  the real surface.

## Audit method (round-2)

For each runtime-side mechanism (M4..M8) plus the held-constant
invariant M9-TX:

1. Locate the canonical enforcement seam in HAI source. Cite file
   path and line range.
2. Describe the *on* semantics: what guard or check fires when the
   mechanism is enabled.
3. Describe the *off* semantics: what behaviour the mechanism would
   show if disabled. Held-constant invariants name "off would corrupt
   the experiment" instead of an ablation contract.
4. Identify coupling: does this mechanism's enforcement implicitly
   depend on another mechanism running first?
5. Rate the mechanism:
   - `clean`: off-path is a single conditional branch on
     `HAI_RUNTIME_MODE`; no other mechanism breaks when this one
     is off.
   - `coupled-today`: code currently entangles this mechanism with
     another; Phase 2 must add a decoupling seam (e.g., dispatch
     enforcer) before independent ablation is possible.
   - `aspirational`: the seam doesn't exist in source today; the
     mechanism is asserted in docs but not enforced. Phase 2 builds
     it.
   - `held-constant`: invariant property; never ablated; off-path
     would corrupt the experiment.
6. Sketch the smallest patch that would add the off-path or, for
   held-constant, the smallest assertion that the invariant remains.

### Rating rubric (resolves the `coupled` vs `aspirational` ambiguity flagged in F-CDX-RFR-R1-14)

- If the current product code already enforces the mechanism in some
  form and can be toggled by guarding existing code paths without
  inventing a new module, rate `clean`.
- If toggling requires touching shared state, another mechanism's
  code, or W57 invariant scaffolding, rate `coupled-today`. The
  follow-up packet must build a decoupling seam.
- If the mechanism is asserted in docs (or in the manifest) but not
  enforced anywhere in code today, rate `aspirational`. The follow-up
  packet must build the enforcement, not just expose a switch.
- If turning off the mechanism would corrupt the system rather than
  produce a measurable comparison, rate `held-constant` and never
  add an off-path.

## Mechanism Records

### M4 — Runtime argument and proposal-payload validation

- **Status:** Audited against source.
- **Canonical seam:** `cmd_propose` loads JSON and calls
  `validate_proposal_dict` before JSONL writeback or DB projection
  (`hai/src/health_agent_infra/cli/handlers/recommend.py:79-140`).
  Proposal schema/action/shape validation lives in
  `hai/src/health_agent_infra/core/writeback/proposal.py:138-292`.
  Final recommendation schema/action/shape validation lives in
  `hai/src/health_agent_infra/core/validate.py:163-254` and is
  called before `BEGIN EXCLUSIVE` in
  `hai/src/health_agent_infra/core/synthesis.py:1060-1083`.
- **On semantics:** malformed proposal payloads and final
  recommendations are rejected before durable writes. `hai propose`
  rejects invalid payloads before JSONL writeback; `run_synthesis`
  rejects invalid final recommendations before the transaction begins.
- **Off semantics:** schema/action/shape invalid payloads can reach
  later layers in hermetic benchmark mode, and the ablation emits a
  `mechanism_disabled` marker naming `validation`.
- **Coupling notes:** the current validators also run the banned-token
  clinical-boundary sweep (`core/writeback/proposal.py:262-271`,
  `core/validate.py:247-254`, shared helper at
  `core/validate.py:406-436`). A naive "skip validate_*" off-path
  would disable part of M7 as well as M4.
- **Coupling rating:** `coupled-today`.
- **Off-path patch sketch:** split schema/action/shape validation from
  clinical-boundary refusal before adding `no_validation`. The
  `no_validation` branch must bypass schema/action/shape checks only;
  it must not silently disable the central M7 refusal seam built by
  `WP-REFUSE-001`.
- **Follow-on packet:** `WP-INV-002` records the M4/M7 split; the
  implementation lands through `WP-REFUSE-001` and `WP-RT-MODE-002`.

### M5 — `agent_safe` enforcement

- **Status:** Audited against source.
- **Canonical seam today:** per-command `agent_safe` metadata is
  attached in the argparse tree (`cli/__init__.py`, for example
  `hai intent commit` at lines 1512-1519, `hai target commit` at
  lines 1659-1666, `hai intake weight` at lines 2118-2125, and
  `hai sync purge` at lines 2316-2323) and emitted by the manifest
  walker (`core/capabilities/walker.py:191-288`, `366-372`). The
  CLI entrypoint dispatches directly to `args.func(args)` after the
  demo gate (`cli/__init__.py:3174-3180`), so there is no general
  dispatch-time `agent_safe` enforcement today.
- **Canonical seam after `WP-DISPATCH-001`:** CLI-dispatch middleware
  that resolves the selected command, reads the parser/manifest
  `agent_safe` flag, and refuses agent-classified callers before the
  handler runs.
- **On semantics after build:** `HAI_INVOCATION_CONTEXT=agent` plus
  `full_contract` refuses every `agent_safe=False` command at dispatch
  with a stable refusal envelope.
- **Off semantics:** `no_agent_safe` bypasses that dispatch refusal in
  hermetic benchmark mode and emits a `mechanism_disabled` marker.
- **Coupling notes:** the only runtime enforcement of an
  `agent_safe=False` surface today is the W57 intent/target
  commit/archive gate, which is M6 rather than general M5. Other
  `agent_safe=False` commands rely on agents honoring the manifest.
- **Coupling rating:** `aspirational` as a general M5 enforcement
  mechanism, with current W57 overlap recorded under M6.
- **Off-path patch sketch:** build the middleware first; the off-path
  is a runtime-mode guard around that middleware, not per-handler
  special casing.
- **Follow-on packet:** `WP-DISPATCH-001` builds the missing M5 seam;
  `WP-INV-003` records the M5/M6 authority split.

### M6 — Proposal/commit separation (W57 user-gate)

- **Status:** Audited against source.
- **Canonical seam:** `_w57_user_gate` in
  `hai/src/health_agent_infra/cli/handlers/intent.py:180-211`;
  `cmd_intent_commit` / `cmd_intent_archive` call it at lines
  214-282. Target commit/archive call the same gate in
  `hai/src/health_agent_infra/cli/handlers/target.py:168-238`.
  Agent-authored target rows are written as `agent_proposed` /
  `proposed` rather than active in `target.py:241-305`.
- **On semantics:** intent/target promotion and deactivation require
  `--confirm` or an interactive TTY. Non-interactive callers get
  `USER_INPUT` before the handler mutates state.
- **Off semantics:** in hermetic benchmark mode only,
  `no_proposal_gate` lets the commit/archive path proceed and emits a
  `mechanism_disabled` marker naming `proposal_gate`.
- **Coupling notes:** the W57 gate is currently the only runtime
  enforcement attached to a subset of `agent_safe=False` commands, so
  it overlaps with M5 until the dispatch enforcer exists. Once
  `WP-DISPATCH-001` lands, M5 becomes command-level dispatch refusal
  and M6 remains promotion/deactivation authority.
- **Coupling rating:** `coupled-today`.
- **Off-path patch sketch:** add an explicit
  `HAI_RUNTIME_MODE == "no_proposal_gate"` branch inside `_w57_user_gate`
  after the hermetic guard is in place. Do not modify target/intent
  storage functions; the gate remains the authority seam.
- **Follow-on packet:** `WP-INV-003` records the M5/M6 split;
  implementation lands through `WP-DISPATCH-001` and `WP-RT-MODE-002`.

### M7 — Refusal contract

- **Status:** Audited against source.
- **Canonical seam today:** no central runtime refusal seam exists.
  Clinical-boundary tokens are defined in
  `hai/src/health_agent_infra/core/validate.py:105-130`; proposal and
  recommendation validators call the shared banned-token sweep
  (`core/writeback/proposal.py:262-271`,
  `core/validate.py:247-254`, helper at `core/validate.py:406-436`).
  The safety skill documents broader refusal policy in
  `hai/src/health_agent_infra/skills/safety/SKILL.md:12-42`.
- **Canonical seam after `WP-REFUSE-001/002`:** a new
  `core/refusal/` module that owns clinical-claim final-output
  refusal and agent-safe-violation refusal envelopes. The banned
  phrase list should be shared with the benchmark scorer.
- **On semantics after build:** output paths and dispatch refusals are
  checked by runtime code before surfacing to the operator.
- **Off semantics:** `no_refusal` bypasses only the central refusal
  seam and emits a `mechanism_disabled` marker. It must not disable
  unrelated schema validation.
- **Coupling notes:** current clinical-token checks are embedded inside
  M4 validators. Phase 2 must separate "schema/action/shape invalid"
  from "clinical-boundary refused" before M4 and M7 can be ablated
  independently.
- **Coupling rating:** `aspirational`.
- **Off-path patch sketch:** introduce `core/refusal/` first; move or
  wrap clinical-boundary decisions there; make `no_refusal` skip that
  module only.
- **Follow-on packet:** `WP-REFUSE-001`, `WP-REFUSE-002`, plus
  `WP-INV-002` for the M4/M7 split.

### M8 — Audit chain (evidence-reference emission, narrowed)

- **Status:** Audited against source.
- **Canonical seam:** `run_synthesis` owns the transactional write path
  (`hai/src/health_agent_infra/core/synthesis.py:767-844`,
  `1137-1279`). Evidence-card emission is a distinct block inside the
  transaction (`synthesis.py:1232-1275`). The row-projector write
  surfaces are in `core/state/projector.py:2168-2502`, especially
  `link_proposal_to_plan`, `project_daily_plan`,
  `project_bounded_recommendation`, `project_planned_recommendation`,
  and `delete_canonical_plan_cascade`. Referential integrity tests live
  in `hai/verification/tests/contract/test_audit_chain_integrity.py`.
- **On semantics:** synthesis writes the proposal/daily-plan/
  recommendation/planned-recommendation/evidence-card graph inside one
  transaction, and read surfaces can cite those evidence references.
- **Off semantics narrowed for ablation:** suppress evidence-reference
  emission only. Daily plan, recommendation, proposal links,
  planned-recommendation rows, X-rule firings, and transaction wrapping
  remain on.
- **Coupling notes:** L5 narration and explanation tasks consume M8
  evidence references. The off-path must never delete or skip the
  state graph itself, because that would collide with M9-TX.
- **Coupling rating:** `clean` after the M8/M9-TX split.
- **Off-path patch sketch:** guard only the evidence-card emission
  block (`synthesis.py:1232-1275`) or a small helper extracted from it
  with `HAI_RUNTIME_MODE != "no_audit_chain"`. Leave
  `BEGIN EXCLUSIVE`, `conn.commit()`, and all core graph writes
  untouched.
- **Follow-on packet:** `WP-RT-MODE-002`.

### M9-TX — Transaction integrity (held-constant invariant)

- **Status:** Audited and held constant. Never ablated.
- **Canonical seam:** `run_synthesis` starts `BEGIN EXCLUSIVE` before
  graph writes and commits/rolls back as one unit
  (`hai/src/health_agent_infra/core/synthesis.py:1137-1279`). The
  module-level contract states the same invariant at
  `synthesis.py:5-22`. Reprojection also uses an exclusive transaction
  in `core/state/projector.py:1185-1202`, `1276-1285`.
- **On semantics:** state-graph writes are atomic; failures roll back
  daily plan, recommendation, planned recommendation, proposal links,
  X-rule firings, and evidence-card writes together.
- **Off semantics:** **DO NOT ABLATE.** Disabling transactions would
  corrupt the state graph and make every runtime-mode result
  uninterpretable.
- **Coupling notes:** transaction integrity is upstream of every
  ablatable mechanism; it remains on even under
  `no_runtime_enforcement`.
- **Coupling rating:** `held-constant`.
- **Off-path patch sketch:** N/A. Runtime-mode tests should assert
  transaction wrapping stays active in every mode.
- **Follow-on packet:** none.

## Coupling graph (source-backed after WP-INV-001)

```text
M4 (validation)        ── currently contains ──> M7 clinical-token checks
M4 (validation)        ── gates before ──> proposal writes and synthesis commit
M5 (agent_safe)        ── aspirational general dispatch seam today
M5 (agent_safe)        ── overlaps today with ──> M6 W57 user gate
M6 (proposal_gate)     ── gates before ──> intent/target commit/archive mutation
M8 (audit_chain)       ── consumed by ──> read surfaces (hai today, hai explain, weekly review)
M9-TX                  ── always-on under all modes ──> wraps M4..M8 writes
```

The empirical correction from WP-INV-001 is the M4/M7 arrow: current
clinical-token checks live inside the validators. Phase 2 must split
that before `no_validation` and `no_refusal` can be interpreted as
independent ablations.

## Hermeticity surface (correction from round 1)

The round-1 plan invented `HAI_STATE_PATH`. That env var does not
exist. The actual existing isolation surface is (per
F-CDX-RFR-R1-11):

| Resource | Env / config | Source |
|---|---|---|
| State DB | `HAI_STATE_DB` | `core/state/store.py` |
| File-backed state base dir | `HAI_BASE_DIR` | `core/paths.py` |
| Threshold / config files | platform config paths + `core/config.py` | `core/config.py:664-686, 834-852` |
| Credentials | OS keyring + env (per pull adapter) | `core/pull/auth.py` |
| Demo / hermetic marker | demo session marker | `core/demo/session.py:1-36, 202-335` |

`WP-HRN-001` (`HAI_HERMETIC=1`) and `WP-HRN-002`
(state/base-dir/config redirection) reframe around these existing
surfaces.

## Out of scope for this file

- M1 (manifest in prompt), M2 (typed action schema), and M3 (harness
  command allowlist) are not audited here. They live in the harness
  or in prompt construction, not in HAI runtime source. They are
  held constant across the headline experiment.
- The `agent_cli_contract.v2` manifest schema bump itself (D-PROJ-017
  (a)) is tracked under Phase 3 packets `WP-MAN-001..006`, not in
  this inventory.
- The benchmark snapshot envelope schema is tracked under
  `BENCHMARK_SPEC.md`, not here.

## Cross-references

- Master plan: `HAI_PAPER_READINESS_EXECUTION.md`.
- Round-1 audit findings: `codex_runtime_first_reframe_audit_response.md`.
- Maintainer responses: `codex_runtime_first_reframe_audit_response_response.md`.
- Phase 2 packets: `WORK_PACKETS.md` (`WP-INV-001`,
  `WP-RT-MODE-001..3`, `WP-REFUSE-001..2`, `WP-DISPATCH-001`).
- Trajectory schema declaring the runtime modes:
  `../../benchmark/governed_agent_bench/schema/trajectory.schema.json`.
- AGENTS.md governance invariants (W57, three-state audit chain).
- Decision record: `../../project/DECISIONS.md` D-PROJ-013..017.
