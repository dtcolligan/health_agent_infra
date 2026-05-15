# Codex Audit Response — Maintainer Closeout (Round 1)

**Round:** 1
**Date authored:** 2026-05-09
**Audit response under review:** `codex_runtime_first_reframe_audit_response.md`
**Verdict received:** `PLAN_INCOHERENT` (20 findings: 2 critical, 17 major, 1 minor)

This file is the maintainer-side closeout of round 1. Each finding
gets one of: `accept`, `accept-with-modification`, `dispute`, or
`defer`. All round-1 findings were accepted. No findings disputed.
Six architectural decisions surfaced by the audit were locked into
`project/DECISIONS.md` D-PROJ-016 and D-PROJ-017 by maintainer
adjudication; this file records the per-finding resolution that
implements those decisions.

## Verdict on the verdict

`PLAN_INCOHERENT` was the right call. The reframe was authored
same-session by one agent; the audit caught real architectural
issues (notably F-02 schema-freeze conflict, F-09/F-10 mechanism
non-orthogonality, F-11 invented env var, F-19 transaction integrity
not held constant) that would have surfaced as expensive bugs during
Phase 1-2 implementation. Round-1 cost: a doc rewrite. Cost if
caught later: weeks of throwaway code.

The empirical settling shape (10 → 5 → 3 → 0 over 4 rounds) is
holding. Round 2 should produce ~3-5 findings; round 3 typically a
nit; round 4 clean. If round 2 produces more than 8, this closeout
introduced second-order issues and the maintainer should re-read the
diff before proceeding.

## Per-finding closeout

### F-CDX-RFR-R1-01 — Active docs still teach the superseded prompt-first experiment

**Resolution:** `accept`.

**Action:** Tombstoned all 11 named docs with round-2 supersession
front-matter and updated the most explicit prompt-first sections.
Specifically:

- `research/runtime_contracts_paper/PAPER_FRAME.md` — note appended.
- `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` —
  note appended; "Systems To Compare" table replaced with
  `runtime_mode × model_class` table.
- `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md` —
  note appended.
- `research/runtime_contracts_paper/BASELINES_AND_ABLATIONS_PLAN.md`
  — Required Conditions table replaced with runtime-first table;
  Scaffold Ablations table reframed as `runtime_mode` values; Stop
  Conditions updated.
- `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md` — note
  appended.
- `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md` — note
  appended; Model Input section rewritten; Conditions table
  replaced with `runtime_mode × model_class` split.
- `benchmark/governed_agent_bench/baselines/README.md` — listing
  replaced with `model_class` table.
- `project/OPERATING_MODEL.md` — note appended.
- `project/HYPOTHESES.md` — H1 restated under runtime-first; H4
  marked future-work per D-PROJ-017 (e); note appended.
- `project/ROADMAP.md` — note appended.
- `README.md` — Benchmark section updated.

### F-CDX-RFR-R1-02 — Manifest v2 work violates the scheduled v0.2.3 freeze

**Resolution:** `accept-with-modification`.

The maintainer's adjudication on this one (D-PROJ-017 (a)) is to
**break the rule**, not to redirect to a benchmark-side envelope.
Reasoning recorded in `DECISIONS.md` D-PROJ-016 + D-PROJ-017: the
v0.2.3 freeze rule's rationale ("stabilize v0.2.x schema additions
before locking") is gone now that HAI is frozen as a product (no
v0.2.x cycles). The clean move is to retire the rule.

**Action:**

- `AGENTS.md` "Settled Decisions" entry on the v0.2.3 capabilities-
  manifest schema freeze: marked retired with date + decision pointer.
- `AGENTS.md` "Do Not Do" entry on freezing the manifest schema
  before v0.2.3: struck through with retirement note.
- `project/DECISIONS.md` D-PROJ-016 + D-PROJ-017 (a) added with
  rationale.
- `WP-MAN-006` (schema bump to `agent_cli_contract.v2`) keeps its
  HAI-source-mutation scope.

### F-CDX-RFR-R1-03 — HAI product freeze not authoritative on disk

**Resolution:** `accept`.

**Action:** D-PROJ-016 added to `project/DECISIONS.md` with full
rationale section. The freeze is now on disk; the memory-side entry
in `project_hai_frozen_2026-05-08.md` becomes informational only.

### F-CDX-RFR-R1-04 — `no_runtime` is a misnamed, confounded condition

**Resolution:** `accept`.

**Action:**

- Renamed to `no_runtime_enforcement` in
  `benchmark/governed_agent_bench/schema/trajectory.schema.json`,
  `score.schema.json`, `task.schema.json`.
- Updated `HAI_PAPER_READINESS_EXECUTION.md`,
  `BENCHMARK_SPEC.md`, `CLAIM_LADDER.md`, `MECHANISM_INVENTORY.md`,
  `WORK_PACKETS.md`, and the schema-contract test.
- The schema-contract test now asserts
  `"no_runtime" not in modes` to prevent regression.

### F-CDX-RFR-R1-05 — `deployment_full` prompt under-specified

**Resolution:** `accept`.

**Action:**

- Versioned prompt template artifact at
  `benchmark/governed_agent_bench/prompts/deployment_full_v1.md`
  with byte-stable system prompt + four named substitutions.
- Trajectory schema now requires `prompt_template_id` and
  `prompt_template_hash` per trajectory.
- Schema-contract test asserts both fields are required.
- The template doc states the byte-freeze policy: edits create
  `deployment_full_v2`, never silent in-place rewrites.

### F-CDX-RFR-R1-06 — Predeclared thresholds asserted, not enforced

**Resolution:** `accept`.

**Action:**

- `score.schema.json` v2: `scorer_config_hash` is now required;
  every metric in `metrics` requires `threshold` (and `threshold`
  cannot be null — the type union is `["number", "boolean"]`).
- Schema-contract test asserts both invariants.
- `CLAIM_LADDER.md` Tier 3 evidence requirement strengthened to
  reference `scorer_config_hash`.

### F-CDX-RFR-R1-07 — Model-scale claim not auditable from schema

**Resolution:** `accept`.

**Action:**

- Trajectory and score schemas v2 add `model_identity` object with
  required `model_family`, `parameter_count`, `quantization`,
  `provider_snapshot`, and `decoding_settings`.
- Conditional schema: `model_identity` is required for every
  non-`rule_baseline` trajectory and score.
- Schema-contract test asserts the conditional.
- `HAI_PAPER_READINESS_EXECUTION.md` model-scale experiment
  description now references a predeclared model roster
  (`benchmark/governed_agent_bench/model_roster.md`, to be
  authored before any model run; not yet committed).

### F-CDX-RFR-R1-08 — M7 refusal not purely aspirational

**Resolution:** `accept`.

The maintainer chose option **3 build it** rather than the split
suggested by Codex. The interpretation: build a centralized
`core/refusal/` runtime seam in Phase 2; existing per-domain
validators may be ported in for consolidation but the deliverable
is one canonical surface, not an incremental augmentation. This is
captured in D-PROJ-017 (c).

**Action:**

- `MECHANISM_INVENTORY.md` M7 entry rewritten: the canonical seam
  is the new `core/refusal/` module. Existing validators noted as
  potentially-portable. Rating: `aspirational` (because the
  canonical seam doesn't exist yet).
- `HAI_PAPER_READINESS_EXECUTION.md` Phase 2 updated.
- `WP-REFUSE-001` and `WP-REFUSE-002` packet language updated.

### F-CDX-RFR-R1-09 — M5 `agent_safe` is not a general runtime enforcement mechanism

**Resolution:** `accept`.

The maintainer chose option **2 build the dispatch enforcer** per
D-PROJ-017 (b), so M5 becomes a real general mechanism rather than
a manifest annotation. This adds ~2-3 weeks to Phase 2.

**Action:**

- New packet `WP-DISPATCH-001` added with full template covering
  the dispatch middleware, the agent/user invocation classification,
  cross-mechanism isolation tests.
- `MECHANISM_INVENTORY.md` M5 entry rewritten: rating
  `aspirational` (general enforcer doesn't exist) plus
  `coupled-today` (current behaviour entangled with W57).
- `HAI_PAPER_READINESS_EXECUTION.md` Phase 2 references
  `WP-DISPATCH-001`.

### F-CDX-RFR-R1-10 — M5 and M6 are not independently meaningful on the write path yet

**Resolution:** `accept`.

Same architectural decision as F-09: D-PROJ-017 (b). After
`WP-DISPATCH-001`, M5 (general dispatch enforcement) and M6 (W57
proposal/commit gate) control different boundaries and are
independently ablatable.

**Action:**

- `MECHANISM_INVENTORY.md` M5 and M6 entries explicitly state the
  current entanglement and the post-`WP-DISPATCH-001` separation.
- Coupling graph in `MECHANISM_INVENTORY.md` updated to show
  "M5 will be separate from M6 (after WP-DISPATCH-001)" alongside
  "M5 overlaps with M6 today."

### F-CDX-RFR-R1-11 — `HAI_STATE_PATH` is not an existing isolation boundary

**Resolution:** `accept`.

**Action:**

- `WP-HRN-002` rewritten to use the real surface: `HAI_STATE_DB`,
  `HAI_BASE_DIR`, demo session marker, platform config paths.
- `HAI_PAPER_READINESS_EXECUTION.md` Phase 4 references the real
  surface and notes the round-1 invented env var.
- `MECHANISM_INVENTORY.md` Hermeticity Surface section enumerates
  the real env vars + Codex source citations.
- New deliverable: `benchmark/governed_agent_bench/HERMETIC_RECIPE.md`
  (recipe doc per `WP-HRN-002` acceptance criteria; not yet
  committed — Phase 4 work).

### F-CDX-RFR-R1-12 — v2 schemas do not encode mandatory invariants

**Resolution:** `accept`.

**Action:**

- `task.schema.json` v2: `load_bearing_mechanisms` and
  `runtime_modes_in_scope` moved to `required` array.
- `trajectory.schema.json` v2: conditional rule:
  `step_type=mechanism_disabled` requires `mechanism`. Also
  `step_type=command` requires `command`.
- `score.schema.json` v2: conditional rule:
  `kind=mechanism_disabled_unexpected` requires `mechanism`.
- Schema-contract test asserts each conditional.

### F-CDX-RFR-R1-13 — `harness_allowlist` leaked a held-constant mechanism into task load-bearing coverage

**Resolution:** `accept`.

**Action:**

- `task.schema.json` v2: `load_bearing_mechanisms` enum is now
  exactly `{validation, agent_safe, proposal_gate, refusal,
  audit_chain}`. `harness_allowlist` removed.
- Schema-contract test asserts: `harness_allowlist` is not in the
  enum; the enum equals the M4-M8 set.

### F-CDX-RFR-R1-14 — Reframe work packets not template-complete

**Resolution:** `accept-with-modification`.

The fix is to expand the reframe packets to the full template **and**
add a rating rubric for `WP-INV-001` per Codex's suggestion. Some
remaining packets (notably the doc packets `WP-DOCS-OPS-001`,
`WP-DOCS-SCAFFOLD-001`, `WP-DOCS-CARD-001`,
`WP-DOCS-CONTRACT-001`) are still summary-only at round-2 close;
those will be expanded before they are assigned to a coding agent.

**Action:**

- `WP-INV-001` packet expanded with full template + rating rubric.
- `WP-MAN-003` expanded.
- `WP-HRN-001` expanded.
- `WP-HRN-002` rewritten and expanded.
- `WP-FIX-002..006` expanded with table of fixture × stress mapping.
- `WP-REFUSE-002` rewritten with hermetic-mode acceptance criteria
  (also addresses F-16).
- New `WP-DISPATCH-001` added with full template.
- `WP-DOCS-OPS-001 / SCAFFOLD-001 / CARD-001 / CONTRACT-001` remain
  summary-only at round-2 close; they will be expanded before
  Phase 8 assignment.

### F-CDX-RFR-R1-15 — Packet dependencies internally inconsistent

**Resolution:** `accept`.

**Action:**

- `WORK_PACKETS.md` now has an explicit dependency graph section
  immediately before the reframe-packets list, showing the chain
  `WP-INV-001 → WP-RT-MODE-001 → WP-RT-MODE-002/003 / WP-DISPATCH-001 / WP-REFUSE-001` etc.
- Per-packet `Dependencies` lines updated to match the graph.

### F-CDX-RFR-R1-16 — `no_agent_safe` acceptance test asks for a W57 violation

**Resolution:** `accept`. This was the most serious safety-flavoured
finding. The round-1 `WP-REFUSE-002` acceptance criteria normalised
a W57 violation by asserting "autonomous `hai intent commit` succeeds
under `no_agent_safe`." This was unsafe even read sympathetically.

**Action:**

- `WP-REFUSE-002` rewritten. New acceptance criteria require:
  - `HAI_RUNTIME_MODE=no_agent_safe` plus `HAI_HERMETIC=1` plus
    `HAI_STATE_DB=/tmp/<fixture>` redirection;
  - the test invokes a representative `agent_safe=false` command
    against a *fixture* DB (or with `--dry-run`);
  - the user's real `~/.hai/` is byte-identical before and after;
  - W57 user-gate still works on user-invoked paths;
  - cross-mechanism isolation: M4, M6, M7, M8 still fire.
- The packet explicitly states: "the packet does not run against
  user state; any test that does is rejected by review."

### F-CDX-RFR-R1-17 — Tier 5 reintroduces the prompt-axis experiment

**Resolution:** `accept`.

**Action:**

- `CLAIM_LADDER.md` Tier 5 moved to a new "Future Work — Appendix
  Tier" section under the heading "Future-A — Fine-Tuned Local
  Operator (relegated from round-1 Tier 5)".
- The appendix explicitly bans the "fine-tuned with vs without
  manifest access" framing as future-work as well — fine-tuning
  experiments must keep the prompt constant and vary the runtime
  mode, the checkpoint, or the recipe.
- `HYPOTHESES.md` H4 marked future-work and rewritten under the
  runtime-first framing (drift robustness, not manifest access).
- Workshop-floor language updated: T0 + partial T1 + at least one
  Tier 2 ranking row, with no fine-tuning dependency.

### F-CDX-RFR-R1-18 — Risk register and calendar omit known first-order risks

**Resolution:** `accept`.

**Action:**

- `HAI_PAPER_READINESS_EXECUTION.md` risk register expanded from
  five rows to nine: added cloud API drift, reproducibility across
  machines, audit-round budget, schema forward-compatibility,
  public-fixture privacy.
- Calendar honesty section rewritten: 12-16 weeks instead of 9-12,
  explicitly budgeting 2-4 weeks for plan-audit loops, and listing
  Phase 2's growth from `WP-DISPATCH-001`.
- Critical-path graph added.
- Scope-cut ladder reordered by cost-of-cutting-after-built rather
  than by conceptual niceness; cut #1 is now "collapse M5+M6"
  rather than "drop M8 audit-chain ablation."

### F-CDX-RFR-R1-19 — M8 audit-chain ablation ignores transaction integrity

**Resolution:** `accept`. This was the architectural finding that
saved the experiment from corruption. Per D-PROJ-017 (d): M9-TX
held-constant.

**Action:**

- `MECHANISM_INVENTORY.md` adds M9-TX as a held-constant invariant
  with explicit "DO NOT ABLATE" semantics.
- M8 entry narrowed: ablatable scope is "evidence-reference
  emission" only; transactions stay wrapped under all modes.
- `HAI_PAPER_READINESS_EXECUTION.md` mechanism table now includes
  M9-TX with held-constant marker.

### F-CDX-RFR-R1-20 — Claim ladder still contains stale prompt-only wording

**Resolution:** `accept` (minor).

**Action:**

- `CLAIM_LADDER.md` Core Research Question rewritten to compare
  "the same model under weaker runtime enforcement" rather than
  "with vs without contract."
- Tier 1 and Tier 2 forbidden-language guards explicitly ban
  "prompt-only baseline" and "manifest-grounded prompting."

## Closing observations

- **No findings disputed.** Round-1 found real issues; the maintainer
  agreed with all of them. The substantive disagreements were on
  *how* to fix two of them (F-02 architectural choice; F-08 build
  vs split), recorded as D-PROJ-017 (a) and (c).
- **Two new packets added** that were not in round 1: `WP-DISPATCH-001`
  (CLI-dispatch enforcer) and the implicit re-scope of `WP-HRN-002`.
- **Schema test count grew from 5 to 13.** The round-2 schemas are
  more strictly validated than round-1; conditional invariants are
  enforced.
- **The empirical settling shape is on track.** Round 1 produced 20
  findings. Round 2's audit (next step) should produce ~3-5 if this
  closeout is honest, or more if it introduced new issues. If round
  2 produces a `PLAN_INCOHERENT`-class issue, re-read the closeout
  diff before responding.

## What this closeout did not do

- **Did not author `WP-DOCS-OPS-001 / SCAFFOLD-001 / CARD-001 /
  CONTRACT-001` to full template.** Those are still summary-only
  and will be expanded before assignment.
- **Did not commit `model_roster.md`** referenced by Tier 3 evidence
  requirements. That is Phase 5/6 work.
- **Did not commit `HERMETIC_RECIPE.md`** referenced by `WP-HRN-002`
  acceptance criteria. That is Phase 4 work.
- **Did not write follow-on `WP-INV-002..N` decoupling packets.**
  Those are emitted from the audit, not pre-allocated.

## Files changed in this closeout

- `project/DECISIONS.md`: D-PROJ-016, D-PROJ-017 added.
- `AGENTS.md`: v0.2.3 schema freeze entries retired.
- `benchmark/governed_agent_bench/schema/{trajectory,score,task}.schema.json`:
  v2 invariants added.
- `benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py`:
  expanded from 5 to 13 tests.
- `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:
  Phase 2 grew, risks + calendar expanded, decisions table grew,
  vocabulary aligned.
- `research/runtime_contracts_paper/MECHANISM_INVENTORY.md`: full
  rewrite with code-grounded picture.
- `research/runtime_contracts_paper/CLAIM_LADDER.md`: Tier 5 to
  Future-A appendix; threshold rigor; forbidden-phrasing guards.
- `research/runtime_contracts_paper/WORK_PACKETS.md`: dependency
  graph; new `WP-DISPATCH-001`; `WP-REFUSE-002` rewritten;
  `WP-HRN-002` rewritten; multiple expansions; rating rubric.
- `benchmark/governed_agent_bench/prompts/deployment_full_v1.md`:
  new versioned prompt artifact.
- `benchmark/governed_agent_bench/BENCHMARK_SPEC.md`: round-2 note
  + mechanism-load-bearing rule already in place from round 1.
- `benchmark/governed_agent_bench/baselines/README.md`: condition
  table replaced.
- `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`:
  Conditions + Model Input rewritten.
- `research/runtime_contracts_paper/{PAPER_FRAME,RESEARCH_EVAL_STRATEGY,PROJECT_EXECUTION_PLAN,BASELINES_AND_ABLATIONS_PLAN,IMPLEMENTATION_PLAN}.md`:
  supersession notes + targeted updates.
- `project/{OPERATING_MODEL,HYPOTHESES,ROADMAP}.md`: supersession
  notes + targeted updates.
- `README.md`: benchmark section updated.

## Round-2 audit prompt

A round-2 audit prompt should be authored as
`codex_runtime_first_reframe_audit_prompt_round_2.md` once this
closeout lands, asking Codex to re-review the diff specifically for:

- whether the M5/M6 separation is actually achieved by
  `WP-DISPATCH-001` as scoped;
- whether the schema invariants in v2 are enforceable in practice
  (i.e., draft 2020-12 conditionals work as expected with the
  validators future scorers will use);
- whether the HERMETIC_RECIPE.md and model_roster.md commitments in
  the EXECUTION doc are honored by deferred packets;
- whether any active doc still teaches prompt-first comparison.
