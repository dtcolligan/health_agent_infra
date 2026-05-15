# Codex Internal Docs Audit v2 - Response

**Verdict:** DOCS_AUDIT_V2_CONFIRMED_WITH_ADDITIONS

**Round:** 1

The second-pass synthesis is directionally correct: the first audit fixed
visible drift and product framing, but the current docs still have factual
drift, routing ambiguity, missing reference surfaces, and several places where
historical cycle artifacts masquerade as current operating docs. I found no
high-severity finding that should be thrown out wholesale. Several require a
different fix shape than the prompt proposed, and I add four findings below.

Step-0 provenance note: `reporting/plans/post_v0_1_15/` currently contains
`README.md` and `internal_docs_audit.md`; the v2 prompt and companion
`internal_docs_audit_v2.md` are not yet on disk. That does not block this
response because the prompt body was provided inline, but it should be closed
before a docs-cycle PLAN is authored.

## Verification of high-severity findings (Q1)

### F-V2-01 - CONFIRMED-WITH-NUANCE

**Evidence:** `reporting/docs/tour.md:99-100` says
`synthesis_policy.py` is "ten X-rule evaluators across Phase A and Phase B."
`reporting/docs/architecture.md:92` says "evaluates X1-X7 against snapshot +
proposals." The authoritative catalogue at `reporting/docs/x_rules.md:49-64`
lists X1a, X1b, X2, X3a, X3b, X4, X5, X6a, X6b, X7, and X9. `non_goals.md`
is not truncated: `reporting/docs/non_goals.md:148-149` already says "10
Phase A rules and one Phase B adjustment rule."

**Recommended fix:** Standardize active prose to "11 X-rules: 10 Phase A
rules plus 1 Phase B adjustment rule." Do not edit `non_goals.md` for this
finding except to keep it as the canonical wording.

### F-V2-02 - CONFIRMED-WITH-NUANCE

**Evidence:** `reporting/docs/recovery.md:1` is titled "Recovery - backup,
restore, and disaster scenarios"; `reporting/docs/recovery.md:3-5` says it is
the v0.1.14 W-BACKUP authoritative recovery contract. `reporting/docs/README.md:45`
routes "Check safety and scope boundaries" to `recovery.md`.

**Recommended fix:** Rename to `backup_and_recovery.md`. The proposed caller
list is incomplete and partly stale: `rg` found live references in
`reporting/docs/README.md:45`, `reporting/docs/agent_cli_contract.md:67`,
and `reporting/plans/post_v0_1_15/internal_docs_audit.md:260`, but not in
root `README.md`, `tour.md`, or `REPO_MAP.md`. Because
`agent_cli_contract.md` is generated, update the capability description source
or renderer input before regenerating.

### F-V2-03 - CONFIRMED

**Evidence:** `reporting/docs/how_to_add_a_domain.md:226-230` says
"Migrations are append-only and numeric-ordered (001...007)" and points to
`004_sleep_stress_tables.sql` and `005_strength_expansion.sql`. The migration
directory currently reaches `025_target_macros_extension.sql`.

**Recommended fix:** Replace with "append-only and numeric-ordered; use the
latest migration number plus one" and cite `state_model_v1.md` for the current
head instead of freezing a range in this tutorial.

### F-V2-04 - CONFIRMED

**Evidence:** `reporting/docs/explainability.md:49-53` says the explain
surface exits `2` for DB-not-initialized, bad selector form, and missing plan.
`reporting/docs/cli_exit_codes.md:16-19` defines `1 = USER_INPUT`,
`2 = TRANSIENT`, and `3 = NOT_FOUND`; `reporting/docs/agent_cli_contract.md:81`
lists `hai explain` as `OK`, `USER_INPUT`, `NOT_FOUND`.

**Recommended fix:** Change explainability to name the taxonomy: caller/input
problems exit `USER_INPUT` and unknown plan ids exit `NOT_FOUND`. Avoid literal
integer codes in prose unless the section is explicitly about the taxonomy.

### F-V2-05 - CONFIRMED

**Evidence:** `CITATION.cff:24-25` says `version: "0.1.8"` and
`date-released: "2026-04-25"`.

**Recommended fix:** Bump to `0.1.15.1` and `2026-05-03`. Also update the
comment at `CITATION.cff:33` if it remains version-specific.

### F-V2-06 - CONFIRMED

**Evidence:** `SECURITY.md:78` says "None as of v0.1.8."

**Recommended fix:** Update to `v0.1.15.1` or make it versionless: "No
published security advisories are currently recorded."

### F-V2-07 - CONFIRMED

**Evidence:** `reporting/docs/privacy.md:126-132` correctly says there is no
first-class "forget one day" command, then incorrectly says that command is on
the v0.1.13 onboarding backlog.

**Recommended fix:** Keep the manual JSONL edit + `hai state reproject`
workaround, and replace the stale backlog sentence with an explicit non-shipped
status and destination only if the maintainer wants to schedule it.

### F-V2-08 - CONFIRMED-WITH-NUANCE

**Evidence:** `README.md:17` has a `tests-2631_passing` badge.
`AUDIT.md:51` in the historical `v0.1.15` entry says "2630 passed, 3 skipped."
`reporting/docs/current_system_state.md:18` says the v0.1.15.1 release gate is
"2631 passed, 3 skipped."

**Recommended fix:** Do not rewrite the historical v0.1.15 audit count to
2631. Instead add the v0.1.15.1 test count to the v0.1.15.1 `AUDIT.md` entry,
and make README/current-system-state the current-count surfaces. I did not run
pytest for this audit because the prompt explicitly said no test runs.

### F-V2-09 - CONFIRMED

**Evidence:** The five entry points use different one-liners:
`README.md:3-4` says "locally governed runtime for personal health agents";
`ARCHITECTURE.md:3-5` says "agent-native" and "deterministic boundaries";
`AGENTS.md:8-12` says "local governance runtime for agentic personal-health
software"; `reporting/docs/architecture.md:3-8` says "agent-native governed
runtime for a multi-domain personal health agent"; and
`reporting/docs/personal_health_agent_positioning.md:15-20` says "agent-native
governed local runtime."

**Recommended fix:** Adopt one canonical opening line and allow the second
sentence to specialize by audience. My preferred line is:
"Health Agent Infra is an agent-native, locally governed runtime for personal
health agents."

## Verification of medium-severity findings (Q2)

### F-V2-10 - CONFIRMED

**Evidence:** All seven cited docs read as cycle artifacts rather than current
operating contracts:

- `calibration_eval_design.md:1-3` is "Calibration eval design (v0.1.14 W-AL)"
  with status "schema/report shape only."
- `cli_boundary_table.md:3-7` is "v0.1.13 W-29-prep" and explicitly says
  "This is a plan, not a contract."
- `demo_flow.md:3-4` is authored for "v0.1.11 W-Z" and calls itself the
  canonical script for that cycle.
- `explain_ux_review_2026_05.md:1-6` is a v0.1.14 W-EXPLAIN-UX review.
- `onboarding_slo.md:1-3` is "W-AA, v0.1.13" and "Target, not gate."
- `source_row_provenance.md:3-8` is v0.1.14 W-PROV-1 and names future
  consumption.
- `supersede_domain_coverage.md:3-8` is a v0.1.12 W-FBC design doc with a
  v0.1.13 named-defer.

**Recommended fix:** Move them out of the current docs index or add an
unmissable `Cycle artifact - not current contract` banner. I prefer moving to
the authoring cycle directories, with a small `reporting/docs/archive/README.md`
only if navigation suffers.

### F-V2-11 - CONFIRMED

**Evidence:** `ls reporting/docs/domains/` shows only `README.md`. There are no
domain reference docs for recovery, running, sleep, stress, strength, or
nutrition.

**Recommended fix:** Add per-domain reference docs, but split the workstream:
start with one template and two pilot domains before committing to six full
reference docs in one pass.

### F-V2-12 - CONFIRMED

**Evidence:** No glossary or terms file exists under `reporting/docs/`.
The vocabulary is dense across current docs; for example
`explain_ux_review_2026_05.md:52-59` records a cold-reader confusion over X9,
and `agent_integration.md:141-158` introduces invariants, forced actions,
phase B, and bundle-only semantics without a glossary surface.

**Recommended fix:** Add `reporting/docs/glossary.md` with 20-30 terms and
short links to the canonical docs. Keep it definitional, not argumentative.

### F-V2-13 - CONFIRMED-WITH-NUANCE

**Evidence:** `rg '^```mermaid|^``mermaid|mermaid' reporting/docs
ARCHITECTURE.md AGENTS.md README.md` returns no matches.

**Recommended fix:** Add diagrams selectively. Good Mermaid candidates:
daily-loop sequence, audit-chain state machine, intent/target lifecycle, and
code-vs-skill boundary. The CLI safety tier is probably clearer as a table.
The per-domain pipeline may be clearer as one ASCII/table hybrid unless it is
kept very small.

### F-V2-14 - CONFIRMED

**Evidence:** The README starts with a 14-row failure-mode table at
`README.md:29-44`, then a 16-row "Current state" table at `README.md:94-110`.
The first install block at `README.md:235-236` leads with the CDN-bypass pinned
install, while the plain `pipx install health-agent-infra` appears later at
`README.md:246-249`.

**Recommended fix:** Add a two-minute path near the top: install, init, inspect
capabilities, run `hai doctor`, run demo or daily. Then move the failure-mode
and current-state tables below the on-ramp or shrink them.

### F-V2-15 - CONFIRMED

**Evidence:** `agent_integration.md:53-94` presents a typical daily loop as a
linear manual sequence and centers `hai synthesize`. The `hai daily` proposal
gate is only explained later at `agent_integration.md:179-187`, including the
`awaiting_proposals`, `incomplete`, and `complete` statuses.

**Recommended fix:** Re-center `hai daily` as the normal agent loop and make
the re-invocation pattern first-class: run daily, fill missing proposals, run
daily again. Keep manual `pull/clean/snapshot/synthesize` as lower-level
debug/operator detail.

### F-V2-16 - CONFIRMED

**Evidence:** `agent_cli_contract.md:23-55` defines mutation classes,
idempotency, and JSON modes. The command table at `agent_cli_contract.md:61`
has an `Agent-safe` column, but no legend defines what `yes` or `no` means.

**Recommended fix:** Update the generator so the generated markdown includes an
Agent-safe legend before the command table.

### F-V2-17 - CONFIRMED-WITH-NUANCE

**Evidence:** `AGENTS.md` is 485 lines. It includes coding-agent orientation
(`AGENTS.md:3-4`), product/runtime description (`AGENTS.md:8-12`), governance
decisions (`AGENTS.md:124-242`), and contribution/session operating rules
throughout the file.

**Argument both sides:** Splitting now would reduce cold-reader load for host
agent integrators and make W57/agent-safe material easier to reuse outside
Claude Code. Against the split: AGENTS.md is the one file coding agents reliably
read at session start, and moving governance fragments too early risks creating
two semi-authoritative contracts.

**Recommended fix:** Defer a hard split. In this docs cycle, add a short
host-agent contract doc or strengthen `agent_integration.md`; later split
AGENTS.md only after a second host integration proves the audience separation.

### F-V2-18 - CONFIRMED

**Evidence:** `how_to_add_a_domain.md` is 22,239 bytes and
`domains/README.md` is 6,566 bytes. Both end with checklists covering domain
file shape, skill, tests, evals, architecture/state-model updates, and X-rule
updates.

**Recommended fix:** Make `domains/README.md` the canonical reference checklist.
Rewrite `how_to_add_a_domain.md` as a tutorial that links to the checklist
rather than repeating it.

### F-V2-19 - CONFIRMED-WITH-NUANCE

**Evidence:** `architecture.md:195-240` enumerates migrations 001-025.
`state_model_v1.md:30-37` names current head 025 and the two newest migration
files. `state_model_v1.md:121-131` is not a migration enumeration; it is a
supporting-table catalogue. The migration files are, correctly, the source of
truth.

**Recommended fix:** Do not keep a full migration ledger in multiple narrative
docs. Keep the current head and latest notable deltas in `state_model_v1.md`;
replace the long `architecture.md` migration list with a link.

## New findings (Q3 - what both audits missed)

### F-V2-NEW-01. Roadmap still names the wrong candidate package

**Severity:** high
**Citation:** `ROADMAP.md:29-30`, `reporting/docs/current_system_state.md:31-34`
**Evidence:** `ROADMAP.md:29-30` says the named candidate installs
`health-agent-infra==0.1.15`; `current_system_state.md:31-34` says the recorded
session runs against `health-agent-infra==0.1.15.1`.
**Recommended fix:** Update `ROADMAP.md` to `0.1.15.1` or explain the pivot
from original v0.1.15 candidate package to hotfixed v0.1.15.1.

### F-V2-NEW-02. `state_model_v1.md` freshness banner undermines its own current head

**Severity:** medium
**Citation:** `reporting/docs/state_model_v1.md:3-9`
**Evidence:** The doc says it is a "human-readable map of the v1 runtime state
model," then says it "was written against the v0.1.8 surface and may lag" while
also naming live migrations 024 and 025.
**Recommended fix:** Replace the v0.1.8 warning with a sharper contract:
"maintained human-readable map; migrations are authoritative for exact DDL."

### F-V2-NEW-03. Install guidance drift between README and agent integration

**Severity:** medium
**Citation:** `README.md:235-249`, `reporting/docs/agent_integration.md:24-31`
**Evidence:** README leads with pinned CDN-bypass `pipx install --force
--pip-args=... 'health-agent-infra==0.1.15.1'`, then says plain `pipx install`
works later. `agent_integration.md:26-31` still leads with plain
`pipx install health-agent-infra` and omits the v0.1.15.1/cache-lag context.
**Recommended fix:** Decide one install story: human quickstart can lead with
plain `pipx`; release-immediate/operator docs can include the pinned bypass.
Then keep README and agent_integration consistent.

### F-V2-NEW-04. Audit-v2 prompt and synthesis are not durable yet

**Severity:** medium
**Citation:** `reporting/plans/post_v0_1_15/`
**Evidence:** Step 0 expected the v2 prompt file, but `ls
reporting/plans/post_v0_1_15/` shows only `README.md` and
`internal_docs_audit.md`.
**Recommended fix:** Save the prompt as
`codex_internal_docs_audit_v2_prompt.md` and save the second-pass synthesis as
`internal_docs_audit_v2.md` before scoping the docs-cycle PLAN.

Additional Q3 checks:

- Opening-line drift extends beyond the five cited entry points:
  `tour.md:10-13` says "agent-native infrastructure"; `reporting/docs/README.md:7-11`
  says "not a health chatbot" and "local governed runtime"; `non_goals.md:3-4`
  opens as a scope-discipline document rather than a product frame. This
  supports F-V2-09 rather than creating a separate finding.
- Stale-fact grep for `v0.1.8`, `v0.1.13`, and `0.1.14` found many legitimate
  historical references, but also supports F-V2-06, F-V2-07, F-V2-10, and
  F-V2-NEW-02. The launch/show-HN docs also contain stale "ten X-rules" prose,
  but outreach material is out of scope for this audit.
- Five sampled cross-links resolve to existing files:
  `HYPOTHESES.md -> reporting/plans/historical/multi_release_roadmap.md`,
  `reporting/docs/README.md -> recovery.md`, `README.md ->
  current_system_state.md`, `how_to_add_a_domain.md ->
  src/.../running-readiness/SKILL.md`, and `REPO_MAP.md ->
  verification/dogfood/README.md`.
- Voice consistency is acceptable inside most files, but not across the doc
  set. README mixes product-positioning prose, operator quickstart, and
  internal release truth; ROADMAP is a dense release ledger; AGENTS is a
  coding-agent operating contract. This is a routing problem more than a line
  edit problem.

## Workstream catalogue audit (Q4)

The catalogue is directionally coherent, but it is too large to execute as one
undifferentiated docs-only cycle. Tiering needs sharpening:

- Tier 1 is mostly honest for factual fixes, but `W-DOC-PROSE` is not purely
  mechanical; README on-ramp, opening-line normalization, and AGENTS prose
  edits are taste-sensitive.
- `W-DOC-RECOVERY-RENAME` should land before `W-DOC-DOMAIN-REF`, because the
  rename frees the `recovery.md` slug for a future recovery-domain reference.
- `W-DOC-ZOMBIE` should land before glossary/domain reference work, because it
  clarifies which docs are current enough to cite.
- `W-DOC-DOMAIN-REF` is really six workstreams plus a template. Treat it as
  Tier 3 or split it into `DOMAIN-REF-TEMPLATE`, `DOMAIN-REF-PILOT`, and
  `DOMAIN-REF-REMAINDER`.
- `W-DOC-DIAGRAMS` should be acceptance-limited: 3-4 diagrams max in the first
  pass, not six diagrams by default.
- The workstream count pushes beyond casual doc-only latitude. It can remain a
  doc-only cycle if it is explicitly tiered and no version bump is required,
  but the PLAN should still use D14-style audit discipline because the docs are
  now product-critical.

Recommended sequencing:

1. Mechanical truth fixes: `W-DOC-FACT-V2`, `W-DOC-RECOVERY-RENAME`,
   `W-DOC-ZOMBIE`.
2. Navigation and reader contract: canonical opening line, 2-minute on-ramp,
   agent-safe legend, install guidance consistency.
3. Structure aids: glossary, selected diagrams, daily-loop rewrite.
4. Heavy reference work: domain docs, worked example, strategic/tactical
   rewrites.

## Non-goals (Q5)

Explicit non-goals for the immediate docs cycle:

- `W-DOC-AGENTS-SPLIT`: defer until at least one non-Claude-Code host
  integration creates real pressure.
- Full six-domain `W-DOC-DOMAIN-REF`: do template + pilot only unless the cycle
  is intentionally expanded.
- `W-DOC-WORKED-EXAMPLE` using real wearable data: defer or use a synthetic
  demo fixture.
- Existing audit `W-DOC-EVAL`: route to v0.1.17 if tied to eval
  implementation; do not write eval philosophy without harness changes.
- Existing audit `W-DOC-STRAT` and `W-DOC-TACTICAL`: keep as separate
  structural planning work unless the maintainer explicitly makes this a larger
  docs cycle.
- Outreach docs: Show HN draft, launch checklist, and screencast script are
  out of scope for this internal-docs audit, though they do contain stale
  X-rule/test-count material that should be swept before public reuse.

## Decision recommendations (Q6)

### D1: Save as audit_v2.md

**Recommendation:** yes
**Reasoning:** The v2 synthesis is now a scope-shaping artifact. Keeping it
only in a chat prompt violates the provenance discipline the repo applies to
code cycles.
**What would change my mind:** If the maintainer decides not to open a docs
cycle and only applies a handful of direct fixes.

### D2: Canonical opening line

**Recommendation:** accept with one small edit
**Reasoning:** Use "Health Agent Infra is an agent-native, locally governed
runtime for personal health agents." It is compact, host-agnostic, and captures
the governance/runtime thesis. Let the next sentence vary by audience.
**What would change my mind:** If the maintainer wants to avoid "agent-native"
for public readers, use the README's plainer "locally governed runtime" at
public entry points and reserve "agent-native" for internal docs.

### D3: Zombie-doc destination

**Recommendation:** move each to its authoring cycle directory
**Reasoning:** These docs have cycle-specific provenance and future-cycle
claims; keeping provenance near the relevant cycle preserves context better
than a generic archive bucket.
**What would change my mind:** If multiple current docs still need stable links
to them; then create `reporting/docs/archive/` with explicit cycle-artifact
banners.

### D4: recovery.md rename target

**Recommendation:** `backup_and_recovery.md`
**Reasoning:** The current file covers backup, restore, export, and disaster
recovery. `backup_restore.md` is too narrow; `disaster_recovery.md` sounds like
enterprise ops and hides routine backup/export.
**What would change my mind:** If the maintainer wants "recovery" reserved only
for the health domain, use `backup_restore_export.md`.

### D5: Workstream destination

**Recommendation:** create `reporting/plans/post_v0_1_15/PLAN.md` as a
docs-only cycle
**Reasoning:** Folding this into v0.1.16 would mix empirical runtime fixes with
docs restructuring. Executing incrementally without a plan would repeat the
problem: good local edits without a coherent reader journey.
**What would change my mind:** If v0.1.16 is delayed and the maintainer wants
only Tier-1 truth fixes now, with Tier-2/3 moved to a later docs plan.

### D6: AGENTS.md split

**Recommendation:** defer
**Reasoning:** The audience overload is real, but the file is also the
session-start contract that keeps coding agents aligned. Split only after a
host-agent integration outside Claude Code proves which content belongs in a
separate machine/host-agent contract.
**What would change my mind:** If a second host integration starts before
v0.1.17, or if AGENTS.md grows beyond the point where coding agents reliably
follow it.

## Provenance verification (Q7)

Spot-checked citations:

- `tour.md:99-100`: "ten X-rule evaluators across Phase A and Phase B" - real.
- `architecture.md:92`: "evaluates X1-X7 against snapshot + proposals" - real.
- `explainability.md:49-53`: "Failure modes the surface exits `2` for" plus
  three bullets - real.
- `privacy.md:131-132`: "single-day forget command is on the v0.1.13
  onboarding cycle backlog" - real.
- `README.md:3-4`: "locally governed runtime for personal health agents" -
  real.
- `ARCHITECTURE.md:3-5`: "agent-native... deterministic boundaries" - real.
- `AGENTS.md:8-12`: "local governance runtime for agentic personal-health
  software" - real.
- `reporting/docs/architecture.md:3-8`: "agent-native governed runtime for a
  multi-domain personal health agent" - real.
- `personal_health_agent_positioning.md:15-20`: "agent-native governed local
  runtime" - real.

Citation corrections against the second-pass research:

- F-V2-01's `non_goals.md` claim should not say the line is truncated; the full
  sentence is present and correct.
- F-V2-02's caller list is not accurate as written. The live references I found
  are `reporting/docs/README.md`, generated `agent_cli_contract.md`, the file
  itself, and the first audit.
- F-V2-19 overstates the state-model duplication. `state_model_v1.md:121-131`
  is a table catalogue, not a migration list.

## The hard problem (Q8)

The asymmetric-audience problem is real, not a research-essay distraction.
Human readers need a short path, examples, and fewer workstream IDs; LLM
session-startups need dense contracts, exact commands, refusal rules, and
provenance. One prose document cannot optimize for both without becoming either
too sparse for agents or too dense for humans.

One-week experiment:

1. Add frontmatter to 3-5 current docs with `audience`, `stability`, `source_of_truth`,
   and `machine_contract` fields.
2. Add one `reporting/docs/host_agent_contract.md` that summarizes the runtime
   contract for non-coding host agents: capabilities, agent-safe, W57,
   daily-loop re-invocation, refusal handling.
3. Keep AGENTS.md unchanged except for one link to that host-agent contract.
4. Add a small doc-freshness test that ensures each `machine_contract: true`
   doc links to its source of truth.

Do not create `AGENTS-MACHINE.md` yet. That name invites a parallel operating
contract before the split has earned itself.

## Open questions for maintainer

- [OQ-DOC-V2-01] Should this response trigger a docs-only PLAN immediately, or
  should Tier-1 truth fixes land first as a small direct cleanup?
- [OQ-DOC-V2-02] Should historical cycle-artifact docs move into their original
  cycle directories, or should they stay under `reporting/docs/archive/` for
  easier browsing?
- [OQ-DOC-V2-03] Is "agent-native, locally governed runtime for personal health
  agents" the canonical opening line, or should public-facing docs avoid
  "agent-native"?
- [OQ-DOC-V2-04] Should the first domain-reference pass cover all six domains,
  or just create a template plus two pilot docs?
