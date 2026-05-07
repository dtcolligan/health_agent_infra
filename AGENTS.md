# AGENTS.md - Runtime Contracts / Health Agent Infra

Briefing for any AI coding agent opening a session in this repo. Read this
first; it is the project-specific operating contract.

## What This Project Is

This repository is organized around runtime-contract research:
can enforceable local software contracts make smaller local models
viable operators for bounded workflows over sensitive user-owned data?

It has three active artifacts:

- **Runtime contract** - the architecture/intervention: capabilities
  manifest, typed commands, mutation classes, `agent_safe`, schemas,
  proposal/commit separation, deterministic gates, policy, and audit.
- **HAI** - the personal-wellness reference runtime, packaged as
  `health-agent-infra` and exposed through the local `hai` CLI.
- **GovernedAgentBench** - the benchmark artifact for contract-governed
  agent operation.

HAI is still active software. A user talks to the host agent in
natural language; the agent operates the local `hai` CLI, reads governed
snapshots, uses packaged skills to compose bounded proposals, and relies on
the Python runtime to validate, reconcile, and commit decisions to local
SQLite state. Under the new project frame, HAI is the reference runtime
and personal wellness is the demonstrator domain, not the whole research
claim.

The unit of shipping is a Python wheel (`health-agent-infra`) plus markdown
skills consumed by the agent at runtime. The maintainer's daily development
loop is Claude Code over this project's own `hai` CLI; the project is its
own dogfood.

**Active repo path.** This contract applies to checkouts at
`/Users/domcolligan/health_agent_infra/`. A stale checkout exists
at `/Users/domcolligan/Documents/health_agent_infra/` (months
behind, head at commit `2811669 Phase H: implement conversational
intake`); ignore it unless explicitly working on historical
provenance. Every session should `pwd` and `git log -1` before
reading or writing planning/source files. (Origin: 2026-05-02
evening; see `reporting/plans/v0_1_15/PLAN.md` §4 item 8 +
codex_plan_audit_response F-PLAN-12.)

Authoritative orientation:

- `PROJECT_FRAME.md` - canonical research framing and priority order
- `PROJECT_OPERATING_MODEL.md` - internal operating model, documentation
  gate, artifact hierarchy, and decision rules
- `HYPOTHESES.md` - current research hypotheses
- `research/runtime_contracts_paper/PAPER_FRAME.md` - locked paper frame
- `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` - current
  project-wide evaluation strategy
- `benchmarks/governed_agent_bench/README.md` - benchmark scope and MVP
- `README.md` - research-facing repo overview
- `reporting/docs/hai_reference_runtime.md` - HAI install, operator
  workflow, domains, and CLI surface
- `ARCHITECTURE.md` - one-page architecture
- `REPO_MAP.md` - every top-level entry classified active/historical
- `reporting/docs/current_system_state.md` - latest shipped truth
  (version, schema head, CLI command count, release posture, next cycle)
- `reporting/docs/architecture.md` - full pipeline and code-vs-skill boundary
- `reporting/docs/non_goals.md` - scope discipline
- `reporting/plans/README.md` - reading-order index for the planning tree
- `reporting/plans/post_v0_1_18/strategic_plan_v2.md` - HAI reference-runtime
  strategy before the research reframe; useful context, not the current
  project-wide priority order
- `reporting/plans/tactical_plan_v0_1_x.md` - HAI reference-runtime backlog
- `reporting/plans/eval_strategy/v1.md` - pre-reframe HAI runtime
  correctness strategy; not project-wide research evaluation
- `reporting/plans/success_framework_v1.md` - pre-reframe HAI value
  framework; not project-wide research success criteria
- `reporting/plans/risks_and_open_questions.md` - pre-reframe HAI risk
  register; useful provenance/support-lane input
- `verification/dogfood/README.md` - persona harness operating guide
- `AUDIT.md` - release-by-release audit index

The 2026-04-25 `reporting/plans/historical/multi_release_roadmap.md`
is SUPERSEDED. Read it only as historical provenance; use the
strategic + tactical plans above for current scope.

## Code Vs Skill

The project has two surfaces. Every contribution lands in exactly one:

- **Python runtime** (`src/health_agent_infra/`) - deterministic, testable
  source of truth for data acquisition, projection, classification bands,
  R-rules, X-rules, synthesis, validation, persistence, and CLI behavior.
- **Markdown skills** (`src/health_agent_infra/skills/`) - judgment layer for
  rationale prose, uncertainty surfacing, clarification, and free-text intake
  routing.

The invariant:

> Skills never mutate actions; code never improvises coaching prose.

If it must be reproducible across model moods, it belongs in Python. If it
is phrasing, framing, or honest uncertainty, it belongs in a skill.

By the time a skill runs, the runtime has already computed
`classified_state` and `policy_result`. A skill that re-derives a band,
score, R-rule, or X-rule firing is a bug.

## CLI Boundaries

Skills and agents mutate state only through `hai`:

- `hai propose --domain <d> --proposal-json <p>` - validate and persist a
  domain proposal.
- `hai synthesize --as-of <d> --user-id <u>` - reconcile proposals and commit
  the daily plan atomically.
- `hai review record --outcome-json <p>` - log an outcome.
- `hai intake gym|nutrition|stress|note|readiness` - record user inputs.
- `hai intent commit --intent-id <id>` and `hai target commit --target-id
  <id>` - promote proposed intent/target rows; these are not agent-safe and
  require explicit user invocation.

Agents must not write directly to `state.db`. The CLI contract is
`hai capabilities --json`; read it rather than guessing.

## Six Domains

`recovery - running - sleep - stress - strength - nutrition`

Each has `domains/<d>/{schemas,classify,policy}.py` and a matching skill.
The synthesis layer (`core/synthesis.py` plus optional
`daily-plan-synthesis` overlay) reconciles the domains.

Nutrition is macros-only in v1. Do not propose food-taxonomy, meal-level, or
micronutrient features without a new scoped plan.

## Governance Invariants

1. **W57 - agent cannot deactivate user state without explicit user commit.**
   Agent-proposed intent/target changes may be proposed, but activation or
   deactivation requires the user-gated commit path.
2. **No autonomous plan generation.** The runtime produces daily
   recommendations over user-authored intent. It does not generate training
   plans or diet plans.
3. **No clinical claims.** No diagnosis-shaped language in recommendations or
   rationales. The safety skill defines the refusal boundary.
4. **Local-first package posture.** State stays in the user's local DB; the
   package has no telemetry path. A hosted agent provider may still receive
   context the user gives that provider.
5. **Three-state audit chain is load-bearing.** `proposal_log` ->
   `planned_recommendation` -> `daily_plan` + `recommendation_log` ->
   `review_outcome` must reconcile through `hai explain`.
6. **Review-summary bool-as-int hardening.** `followed_recommendation`,
   `self_reported_improvement`, and `policy.review_summary` runtime threshold
   values reject bool-shaped numeric inputs. v0.1.10 W-A extended the
   hardening across nutrition policy + classify + synthesis_policy x7/x2/
   x3a/x3b. Use `core.config.coerce_int / coerce_float / coerce_bool` for
   any new threshold-consumer site (D12).

## Settled Decisions - Do Not Reopen Casually

These were decided across audit cycles. If you think one needs revisiting,
write a cycle proposal in `reporting/plans/`; do not act unilaterally.

- **W37 original shape is dead.** Skills do not compute review-outcome
  pattern tokens. W48 replaced it with code-owned
  `core/review/summary.py`.
- **W39 narrowed.** Threshold override loading already exists. v0.1.8 scope
  was validation/diff/auditability, not re-implementation.
- **W47 is cut.** Keep release-proof/changelog discipline, but do not add a
  working-tree-sensitive changelog test.
- **W29 / W30 scheduled.** cli.py split scheduled for **v0.1.17**
  (deferred from v0.1.14 at the 2026-05-01 pre-implementation gate;
  v0.1.13 W-29-prep boundary-audit verdict was green and the
  parser/capabilities regression test landed, so the mechanical
  split itself is the deliverable; redestination v0.1.15 → v0.1.17
  on 2026-05-02 evening per the v0.1.15 scope-restructure round-0
  self-audit — see `reporting/plans/v0_1_15/PLAN.md` §1.4 and
  `reporting/plans/v0_1_17/README.md`). Capabilities-manifest
  schema freeze scheduled for **v0.2.3** after all v0.2.x schema
  additions land (**W52 + W58D claim-block (v0.2.0), W53 (v0.2.1),
  W58J (v0.2.2)**). (Origin: v0.1.12 CP1 + CP2, paired acceptance;
  v0.2.x destination updated by post-v0.1.13 CP-PATH-A +
  CP-W30-SPLIT, OQ-B answered Path A 2026-05-01; W58D claim-block
  added to v0.2.0 schema-group list per v0.1.14 D14 round 1
  F-PLAN-10; v0.1.14 → v0.1.15 W-29 destination updated 2026-05-02
  mid-day post-v0.1.14.1 ship; v0.1.15 → v0.1.17 W-29 destination
  updated 2026-05-02 evening per scope-restructure self-audit, so
  v0.1.15 can ship the foreign-user-ready package without W-29 merge
  friction with W-A/W-C/W-D CLI extensions; v0.1.17 promoted to
  next-active cycle 2026-05-04 after v0.1.16 cancelled — named
  foreign-user candidate unavailable, foreign-user empirical work
  renumbered to v0.1.19, with new v0.1.18 onboarding cycle inserted
  before it; W-29 destination unchanged at v0.1.17. See
  `reporting/plans/v0_1_16/README.md`,
  `reporting/plans/v0_1_18/README.md`, and
  `reporting/plans/v0_1_19/README.md`. **W-29 closed at v0.1.17**
  (mechanical split landed; cli.py 9927 LOC → 1 main + 1 shared +
  11 handler-group modules, all <2500 LOC; manifest byte-stable;
  refreshed boundary note at
  `reporting/plans/v0_1_17/w29_boundary_refresh.md`). W-30 regression-
  test scaffold landed at v0.1.17; capabilities-manifest schema freeze
  itself remains scheduled for v0.2.3 per the unchanged provenance
  chain above.)
- **Garmin Connect is not the default live source.** Login is rate-limited
  and unreliable. Default to intervals.icu when configured. As of
  v0.1.14.1 (W-GARMIN-MANIFEST-SIGNAL), this is also a *structured*
  signal: `hai capabilities --json` exposes
  `commands[hai pull].flags[--source].choice_metadata.garmin_live.reliability == "unreliable"`,
  and `_resolve_pull_source` emits a stderr warning at resolution
  time when the resolved source is `garmin_live`. Agents reading the
  capabilities manifest programmatically should pattern-match on
  `choice_metadata` rather than parsing the help-text prose.
- **Nutrition v1 is macros-only.**
- **No `STATUS.md`.** Status lives in CHANGELOG, AUDIT, ROADMAP, and
  ARCHITECTURE; do not resurrect a parallel status file without a new
  maintainer decision.
- **(D10, v0.1.10) Persona harness lives in `verification/dogfood/`,
  not `verification/tests/`.** Full matrix runs are not part of CI. CI
  stays fast; persona matrix is invoked on release.
- **(D11, v0.1.10) Pre-PLAN bug-hunt phase is permanent pattern.**
  Substantive releases run a structured hunt (internal sweep +
  audit-chain probe + persona matrix + Codex external audit) before
  scoping PLAN.md. Findings consolidate to `audit_findings.md`.
- **(D12, v0.1.10) Every `int(cfg)` / `float(cfg)` / `bool(cfg)` in the
  runtime must use `core.config.coerce_*` helpers.** Bool-as-int silent
  coercion is the highest-impact silent bug class. New code referencing
  thresholds without going through the helpers is a bug.
- **(D13, v0.1.11) Threshold-injection seam is trusted-by-design.**
  Production callers always validate user-supplied thresholds via
  `core.config.load_thresholds`, which runs `_validate_threshold_types`
  at the user-TOML boundary. Every `evaluate_*_policy` /
  `classify_*_state` entry point accepts a `thresholds: Optional[dict]`
  arg, but in-memory construction + direct pass-through is reserved for
  tests (trusted by design) and intentional defensive paths. New
  non-test code that constructs threshold dicts and bypasses
  `load_thresholds` is a code-review concern. Defensive D12 coercer use
  at consumer sites is the second line of defence. Origin: v0.1.11 W-T
  audit (Codex round 3 SHIP_WITH_NOTES note 1, F-CDX-IR-R3-N1). See
  `reporting/plans/v0_1_11/W_T_audit.md` for the call-site survey.
- **(D14, v0.1.11) Pre-cycle Codex plan-audit is permanent pattern for
  substantive PLAN.md revisions.** Before Phase 0 (D11) bug-hunt opens,
  Codex reviews PLAN.md against a `codex_plan_audit_prompt.md` and
  returns one of `PLAN_COHERENT` / `PLAN_COHERENT_WITH_REVISIONS` /
  `PLAN_INCOHERENT`. Maintainer responds; PLAN.md revises until verdict
  is positive. **Multiple rounds are normal** — round 2 typically catches
  second-order contradictions introduced by round-1 revisions. Phase 0
  (D11) runs against the final plan-audited PLAN, with an explicit
  pre-implementation gate after `audit_findings.md` consolidates —
  Phase 0 findings tagged `revises-scope` may revise the plan further;
  findings tagged `aborts-cycle` may end the cycle. Implementation does
  not start until that gate fires. Doc-only and small-scope releases may
  skip D14 (same threshold as D11). Origin: v0.1.11 cycle. Round 1
  caught 10 substantive findings (including 2 fail-open correctness
  bugs and a wrong file path) before any code changed; round 2 caught
  5 second-order contradictions from round-1 revisions (W-Vb deferral
  not propagating, demo archive vs byte-identical-tree gate,
  refused-and-required `--deep`, JSONL row-drop bug, frozen-schema
  wording); round 3 caught 3 stale propagation clauses from round-2
  revisions (W-Z catalogue/sequencing hard-deps on W-Vb stale,
  W-Vb acceptance archive path stale, top-level ship gate frozen-
  schema wording stale); round 4 verdict was `PLAN_COHERENT` with no
  findings. **Empirically, 4 rounds was the full settling time for a
  substantive PLAN.md** (14 → 20 workstream growth + cross-cutting
  demo-isolation + audit-chain-integrity work). Future cycles should
  budget 2-4 rounds rather than expecting one-shot coherence. All
  four rounds were cheap relative to catching the same bugs during
  implementation. **v0.1.12 confirmed the 10 → 5 → 3 → 0 settling
  signature** at the same 4-round shape (18 cumulative findings) —
  the pattern is now twice-empirically-validated for substantive
  PLANs.
- **(D15, v0.1.12) Cycle-weight tiering.** Substantive / hardening
  / doc-only / hotfix.

  - **Substantive** (≥1 release-blocker workstream, ≥3 governance
    or audit-chain edits, OR ≥10 days estimated): full Phase 0
    bug-hunt (D11) + multi-round D14 plan-audit until
    `PLAN_COHERENT` (empirical norm 2-4 rounds).
  - **Hardening** (correctness/security only, no governance, ≤1
    week): abbreviated Phase 0 (internal sweep + audit-chain
    probe; persona matrix optional); single-round D14 plan-audit
    target.
  - **Doc-only** (no code change, no test surface change): may
    skip Phase 0 + D14. RELEASE_PROOF still required if version
    bumps.
  - **Hotfix** (reverts, single-bug fixes, named-defer
    propagation, no scope expansion): may skip Phase 0 + D14.
    Lightweight RELEASE_PROOF.

  RELEASE_PROOF.md declares the chosen tier as the first line
  of the document. Future audit-cycle retros cite the tier
  annotation. Origin: v0.1.12 CP3.
- **(D16, post-v0.1.18) W-2U-GATE split.** Foreign-user empirical
  evidence is three gates, not one. **W-2U-INSTALL** (install +
  onboarding + abstain-without-wearable produces coherent output for
  a non-maintainer) is closed by the post-v0.1.18 foreign-user
  session (maintainer's father, 2026-05-06; verbal-only closure, no
  transcript). **W-2U-WEARABLE** (full pipeline produces useful
  output for a wearable-bearing foreign user) and **W-2U-DOGFOOD**
  (non-maintainer uses the system daily for ≥7 consecutive days) are
  deferred to opportunistic-not-blocking from v0.2.0 forward, both
  re-evaluated as hard gates at the v0.4 review when MCP read-surface
  decisions require foreign-user evidence. v0.2.0 hard-deps drop the
  foreign-user empirical row; v0.2.0's only remaining hard dep is
  v0.1.14 substrate (W-PROV-1 + W-AJ). The named residual: v0.2.0
  ships its W52 weekly-review surface without a wearable-bearing or
  multi-day foreign-user session having run against it; the W58D
  factuality gate is the structural mitigation. The W-2U-INSTALL
  closure is verbal-only and a future cycle's D14 may flag this as
  weak provenance. Origin: post-v0.1.18 CP-2U-GATE-SPLIT
  (`reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`).
- **(D17, 2026-05-07) Research reframe is canonical.** The repo's
  active objective is the runtime-contract paper plus
  GovernedAgentBench. HAI continues as the personal-wellness reference
  runtime, but HAI v1 polish is subordinate unless it directly supports
  the paper, benchmark, contract freeze, or reproducible baselines.
  The paper frame is conservative and measurement-first: architecture
  first, benchmark second, experiments third. The health boundary is
  non-clinical by design (no diagnosis, treatment, prescribing, or
  autonomous medical decisions). Do not reopen HACO-Bench naming or
  health-agent-first framing without an explicit maintainer decision.
  Canonical sources: `PROJECT_FRAME.md`,
  `PROJECT_OPERATING_MODEL.md`, `HYPOTHESES.md`,
  `research/runtime_contracts_paper/PAPER_FRAME.md`, and
  `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`.
- **(D18, 2026-05-07) Documentation alignment is the current gate.**
  After the research reframe, do not assume implementation work should
  resume just because the root README changed. The repo must be
  internally engineered for the new goal first: cold-start docs,
  project-wide hypotheses, evaluation strategy, roadmap, and HAI
  planning provenance must all agree on the new objective. Canonical
  gate: `PROJECT_OPERATING_MODEL.md`.

## Release Cycle Expectation

Substantive releases run structured Codex audit/response rounds under
`reporting/plans/v0_1_X/`. v0.1.8 stabilized the four-round pattern;
v0.1.10 added the pre-PLAN bug-hunt phase (D11); v0.1.11 added the
pre-cycle plan-audit phase (D14):

-1. **Pre-cycle Codex plan-audit** (v0.1.11+, D14). Codex reviews
    PLAN.md against `codex_plan_audit_prompt.md`. Maintainer responds;
    PLAN.md revises until verdict is `PLAN_COHERENT`.
0. **Pre-PLAN bug hunt** (v0.1.10+, D11). Internal sweep + audit-chain
   probe + persona matrix + Codex external audit run against the
   plan-audited PLAN.md. Findings consolidate to `audit_findings.md`
   with `cycle_impact` tags. Optional for doc-only / small-scope
   releases; required for substantive ones.
0a. **Pre-implementation gate.** Maintainer reads `audit_findings.md`.
    `revises-scope` findings may revise PLAN.md (loop back to D14 if
    the revision is large). `aborts-cycle` findings may end the cycle.
    Implementation does not start until this gate fires.
1. `PLAN.md` (now plan-audited and bug-hunted) names the release scope.
2. `codex_audit_prompt.md` -> `codex_audit_response.md` records round 1.
3. Maintainer response files address findings with code changes, deferrals,
   or explicit disagreement.
4. Subsequent implementation-review rounds continue until the verdict is
   `SHIP` or `SHIP_WITH_NOTES`.
5. `RELEASE_PROOF.md` and `REPORT.md` record the final state.

Do not ship a substantive release without release proof. Smaller doc-only
changes can be scoped by Dom, but do not silently weaken the audit
convention.

### Ship-time freshness checklist (v0.1.12 W-AC / reconciliation A8)

Before declaring a substantive release shipped, verify every line below.
Drift in any of these is the trust hazard a second user hits first:

- [ ] `ROADMAP.md` "Now" section names the just-shipped version + the
  current in-flight version. No "v0.1.X current" string for an older X.
- [ ] `AUDIT.md` has a new entry for the just-shipped cycle (round table +
  outcome verdict + RELEASE_PROOF link). v0.1.10/v0.1.11/etc. cannot
  silently fall off the index.
- [ ] `README.md` reflects the research frame and current artifact status.
- [ ] `PROJECT_OPERATING_MODEL.md`, `HYPOTHESES.md`, and
  `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` still
  reflect the current objective.
- [ ] `reporting/docs/hai_reference_runtime.md` reflects HAI install,
  operator workflow, domains, and CLI surface.
  Historical "v0.1.X added Y" prose can stay.
- [ ] `PROJECT_FRAME.md` and
  `research/runtime_contracts_paper/PAPER_FRAME.md` still match any
  project-priority or paper-framing changes.
- [ ] `reporting/docs/current_system_state.md` reflects the just-shipped
  package version, schema head, command count, test gate, and next-cycle role.
- [ ] `reporting/plans/README.md` reading-order index marks the just-
  shipped cycle as shipped (not "in flight").
- [ ] `reporting/plans/tactical_plan_v0_1_x.md` next-cycle row reflects
  the just-authored next-cycle PLAN, not the pre-revision shape.
- [ ] `reporting/plans/success_framework_v1.md`,
  `reporting/plans/eval_strategy/v1.md`, and
  `reporting/plans/risks_and_open_questions.md` are still clearly marked
  as HAI pre-reframe/support-lane docs, not current project-wide
  strategy.

`verification/tests/test_doc_freshness_assertions.py` (added v0.1.12)
catches version-tag drift in the most common offenders mechanically.
The checklist above covers the human-judgement freshness items the
test cannot mechanise.

## Patterns the cycles have validated

Operating-discipline lessons surfaced through audit chains. These
apply to every AI agent (Claude Code, Codex, future tools); failure
to apply them is the canonical shape of an audit-round finding.

### Provenance discipline

Before citing a file path, line number, function name, or fact in a
PLAN, RELEASE_PROOF, audit response, or reply to the maintainer,
**verify on disk**. Empirical examples:

- v0.1.12 D14 round 2 caught `core/credentials.py:171` claims when
  the helper actually lived at `core/pull/auth.py:171`.
- v0.1.12 D14 round 2 caught "strategic plan §10 contains no MCP
  exposure row" when it had a Wave 3 row at line 444.
- v0.1.12 IR round 1 caught W-FBC RELEASE_PROOF claims of "recovery
  prototype shipped" when only the flag plumbing landed.

Verify by reading or grepping the actual file; do not trust the
previous round's assertion. Verify *file paths*, *line numbers*,
*function/class names*, and *exact strings* before citing them.

### Summary-surface sweep on partial closure

When a workstream ships partial closure or fork-defers, **all
summary surfaces must move in lockstep**, not just RELEASE_PROOF.
The canonical sites that must reflect the partial scope:

- `PLAN.md` §1.1 theme bullet
- `PLAN.md` §1.2 catalogue row (severity / files / source)
- `PLAN.md` §1.3 deferral table
- `PLAN.md` §2.X per-WS contract section
- `PLAN.md` §3 ship-gate row
- `PLAN.md` §4 risks register entry
- `RELEASE_PROOF.md` §1 workstream completion row
- `RELEASE_PROOF.md` §5 out-of-scope items
- `REPORT.md` §3 highlights + §4 deferrals + §6 lessons
- `CARRY_OVER.md` §1/§2/§3 disposition rows
- `ROADMAP.md` "Now" / "Next" rows
- `reporting/plans/tactical_plan_v0_1_x.md` §3.1 / §3.2 / §4
- `CHANGELOG.md` bullet
- Any `reporting/docs/<workstream>.md` design doc
- CLI help text (if a flag/command was scoped down)

Missing one is the canonical IR-round-2-finds-it bug. Origin:
v0.1.12 IR rounds 1 + 2.

### Honest partial-closure naming

When a workstream undershoots, **name the residual with destination
cycle** in every artifact. Convention:

- `in-cycle (W-X here)` → `partial-closure → v0.1.X+1 W-X-2`
- `full broader gate ships` → `fork-deferred → v0.1.X+1 W-X`

Don't dress up partial work as full delivery. The audit chain
catches the mismatch every time; the only difference is whether
you save a round by being honest first. Origin: v0.1.12 W-Vb +
W-FBC + W-N-broader.

### Audit-chain empirical settling shape

Twice-validated across v0.1.11 and v0.1.12:

- **D14 plan-audit:** 4 rounds, **10 → 5 → 3 → 0** findings.
  Budget 2-4 rounds for substantive PLANs; 1 round for hardening
  or doc-only.
- **Implementation review:** 3 rounds, **5 → 2 → 1-nit**.
  Budget 2-3 rounds for substantive cycles.

If round N has *more* findings than round N-1, the previous
response introduced second-order issues — re-read your own diff.
A "1-shot" estimate on a substantive PLAN is wrong; round 2
always finds something round 1 introduced.

### Cycle-prompt templates

Future cycles should not author Codex audit prompts from scratch.
Templates live at:

- `reporting/plans/_templates/codex_plan_audit_prompt.template.md`
- `reporting/plans/_templates/codex_implementation_review_prompt.template.md`

Copy the relevant template into the cycle dir and customise the
"Why this round" + step-1 reading list + step-2 audit questions
for the cycle's actual workstream catalogue. Step 0 / step 3 /
step 4 / step 5 / step 6 / step 7 stay stable across cycles.

## Test Commands

```bash
uv run pytest verification/tests -q
uv run pytest verification/tests/test_<area>.py -q
uv run python -m build --wheel --sdist     # if packaging changed
uv run hai capabilities --json             # if CLI surface changed
uv run hai doctor                          # if migrations/state changed
```

CI runs `verification/tests/`. The suite includes docs and skill/CLI drift checks.

## Architectural Seams

| Concern | Lives in |
|---|---|
| New domain | `src/health_agent_infra/domains/<d>/` plus a sibling skill |
| New pull source | `src/health_agent_infra/core/pull/`; see `reporting/docs/how_to_add_a_pull_adapter.md` |
| Cross-domain logic | `src/health_agent_infra/core/synthesis.py` and `synthesis_policy.py` |
| New CLI command | `src/health_agent_infra/cli.py`; annotate capabilities metadata |
| New audit field | Add to the write path and to `hai explain` rendering |
| New skill | `src/health_agent_infra/skills/<name>/SKILL.md` with valid frontmatter |
| New persona archetype | `verification/dogfood/personas/p<N>_<slug>.py` + register in `personas/__init__.py`'s `ALL_PERSONAS` |
| New threshold consumer | Always use `core.config.coerce_int / coerce_float / coerce_bool` (D12) |

## Do Not Do

- Do not bypass the `hai` CLI for mutations.
- Do not compute bands, scores, R-rules, or X-rule firings inside a skill.
- Do not make clinical claims.
- Do not generate training or diet plans.
- Do not deactivate user-authored state without explicit user commit.
- Do not import from `skills/` inside Python runtime code.
- Do not add a write path that bypasses the three-state audit chain.
- Do not open a PR or push autonomously.
- Do not add a wearable source until the per-domain evidence contract is
  broadened.
- Do not freeze the capabilities manifest schema before its scheduled
  cycle (v0.2.3). (Origin: v0.1.12 CP1 + CP2; v0.2.x destination updated
  by post-v0.1.13 CP-W30-SPLIT; v0.1.14 → v0.1.15 cli.py-split
  destination updated 2026-05-02 mid-day post-v0.1.14.1 ship;
  v0.1.15 → v0.1.17 destination redestinated 2026-05-02 evening per
  the v0.1.15 scope-restructure self-audit to keep the foreign-user-
  ready package cycle free of cli.py merge friction with W-A/W-C/W-D
  CLI extensions — see `reporting/plans/v0_1_15/PLAN.md` §1.4 and
  `reporting/plans/v0_1_17/README.md`; v0.1.17 promoted to next-active
  cycle 2026-05-04 after v0.1.16 cancelled, foreign-user empirical
  work renumbered to v0.1.19 with new v0.1.18 onboarding cycle before
  it — destination unchanged at v0.1.17. **W-29 cli.py-split clause
  retired at v0.1.17 ship — the split landed cleanly with byte-stable
  manifest; this entry is provenance only. Capabilities-manifest
  schema-freeze clause retained until v0.2.3.**)
- Do not add micronutrient or food-taxonomy features.
- Do not treat HAI v1 polish as the default next priority when a
  paper-critical benchmark, contract, or experiment task is available.
- Do not frame this repo as a consumer health-product bet; the active
  external artifact is research engineering (paper + benchmark +
  reference runtime).
- Do not treat raw SQLite reads as the normal inspection surface; use
  `hai today`, `hai explain`, and `hai doctor`.
- Do not anchor a data path on Strava — directly or via an upstream
  that proxies Strava data. Strava's Nov 2024 API agreement
  prohibits AI/ML use of Strava data; intervals.icu was specifically
  named. (Origin: post-v0.1.13 strategic research §15 D-4 +
  CP-DO-NOT-DO-ADDITIONS.)
- Do not ship a mechanism that auto-loads MCP servers from project
  files (e.g., `.claude/settings.json` referencing a hai-managed MCP
  server). HAI runs inside Claude Code; CVE-2025-59536 /
  CVE-2026-21852 (Check Point) demonstrate the project-file
  autoload + token-exfiltration chain. Manual install + local stdio
  is the only allowed exposure path. (Origin: post-v0.1.13
  strategic research §17 Sc-5 + CP-DO-NOT-DO-ADDITIONS.)
- Do not allow automatic threshold mutation by an LLM agent without
  an explicit user-commit step. The v0.7 governed-adaptation
  surface requires user approval per recommendation; any drift
  toward "the agent retunes thresholds based on outcomes" is a
  hidden learning loop, prohibited by ROADMAP.md "Explicitly Out
  Of Scope" + W57 governance invariant. (Origin: post-v0.1.13
  strategic research §18 + CP-DO-NOT-DO-ADDITIONS.)

## When In Doubt

Read `PROJECT_FRAME.md`, `PROJECT_OPERATING_MODEL.md`,
`research/runtime_contracts_paper/PAPER_FRAME.md`,
`research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`,
`HYPOTHESES.md`, `README.md`, `REPO_MAP.md`, `ROADMAP.md`,
`reporting/docs/architecture.md`, and `reporting/docs/non_goals.md`. If
the question is about HAI operation, also read
`reporting/docs/hai_reference_runtime.md`. If the question is about HAI
release history, then read `reporting/plans/README.md` and the relevant
cycle plan. If still unclear, ask Dom rather than guessing.

The planning tree under `reporting/plans/` has a structured shape as of
2026-04-29:

- `post_v0_1_18/strategic_plan_v2.md` — HAI reference-runtime strategy
  before the research reframe.
- `tactical_plan_v0_1_x.md` — HAI reference-runtime backlog.
- `eval_strategy/v1.md` — pre-reframe HAI correctness strategy.
- `success_framework_v1.md` — pre-reframe HAI value framework.
- `risks_and_open_questions.md` — pre-reframe HAI risk register.
- `v0_1_X/` — per-cycle artifacts (PLAN, audit findings, release proof).
- `historical/` — superseded planning docs (multi_release_roadmap,
  post_v0_1_roadmap, agent_operable_runtime_plan, launch_notes,
  skill_harness_rfc, phase_0_*, phase_2_5_*). Provenance only.
- `future_strategy_2026-04-29/` — Claude/Codex deep strategy review +
  reconciliation. Drives the v0.1.12+ refresh.

The `reporting/plans/README.md` index disambiguates which doc to read
when. Always check there before authoring a new plan doc.
