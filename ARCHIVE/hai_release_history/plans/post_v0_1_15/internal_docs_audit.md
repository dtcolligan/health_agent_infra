# Internal Docs Research Audit - post-v0.1.15

**Date:** 2026-05-03
**Trigger:** v0.1.15 and v0.1.15.1 shipped, then the maintainer
flagged that the internal docs were not explaining the product as well
as the code, audit chain, and release discipline deserved.
**Scope:** root docs, `reporting/docs/`, planning indexes, current
cycle workspaces, generated CLI contract docs, skills, and verification
docs. Frozen historical audit artifacts were read for provenance but
were not rewritten unless they were being used as current navigation
surfaces.
**Method:** local doc inventory, cross-doc stale-term sweep, three
parallel sub-audits over docs/planning/skills, and an external research
pass over current agent-runtime documentation patterns.

## Verdict

The repo had strong evidence and weak routing. The audit chain proves
that the runtime is unusually disciplined, but a reader had to infer the
product from release proofs, workstream plans, audit responses, and
skills. That is the wrong shape for a project whose value proposition is
itself about turning agent behavior into governed infrastructure.

The highest-value correction is to make the docs say the product thesis
plainly:

Health Agent Infra is a locally governed runtime for personal health
agents. It gives a shell-capable agent a local health state database,
typed read/write surfaces, deterministic projections, human gates, audit
trails, and refusal boundaries. Claude Code is the first compatible host,
not the long-term product boundary.

This pass fixes the most damaging current-facing drift and improves the
operator-facing docs. It does not try to rewrite every strategic or
historical document. Those should become a named docs cycle because the
remaining work is structural, not a patch.

## External Research Lens

The external docs point in the same direction: strong agent products
explain the runtime contract before the feature list.

- Anthropic's personal-guidance research shows both demand and risk:
  roughly 6% of sampled Claude conversations were personal guidance, and
  health and wellness was the largest guidance domain at 27% of guidance
  conversations. The article also names sycophancy, one-sided framing,
  high-stakes health/finance/legal guidance, and inaccessible human
  fallback as evaluation targets. Source:
  https://www.anthropic.com/research/claude-personal-guidance
- LangGraph documents persistence as a first-class capability because
  checkpoints enable human-in-the-loop workflows, memory, replay, and
  fault tolerance. That validates making HAI's local state database,
  snapshots, replay, migrations, and backup story part of the top-level
  product explanation rather than burying them in architecture docs.
  Source: https://docs.langchain.com/oss/javascript/langgraph/persistence
- OpenAI Agents SDK docs separate guardrails and tracing as named
  primitives. That maps directly to HAI's W57 human gates, agent-safe CLI
  annotations, X-rule firings, `hai explain`, and refusal surfaces.
  Sources: https://openai.github.io/openai-agents-js/guides/guardrails/
  and https://openai.github.io/openai-agents-python/tracing/
- MCP frames agent integration around explicit host/client/server/tool
  contracts. HAI should keep moving in that direction: the important
  doc artifact is not a prose list of commands, but the generated
  capability contract and the rules for which commands are agent-safe.
  Source: https://modelcontextprotocol.io/docs/learn/architecture
- Human-in-the-loop decision-infrastructure products consistently sell
  the accountability boundary: automation continues until a sensitive
  decision needs explicit authority. HAI's local version of this is W57
  plus proposal/commit separation, and the docs should name it directly.

## Top Findings

### F-DOC-01. Product Framing Was Buried

**Severity:** high
**Status:** fixed in current orientation docs.

Before this pass, the README had pieces of the right argument but did
not consistently name the failure cases the runtime solves:

- agents lack a durable local health state;
- agents can improvise interpretation and write paths;
- agents can validate their own outputs without a separate policy layer;
- agents can over-personalize or sycophantically validate user framing;
- agents can blur the difference between proposal, review, and commit;
- agents can make health claims without calibrated data, targets, or
  escalation boundaries.

The README now leads with those failure modes, then explains where the
product stands today, what the daily loop does, and how weekly review,
planning, and future loops build on the same infrastructure.

### F-DOC-02. Claude Code Was Overstated As The Product Boundary

**Severity:** high
**Status:** fixed across the main current-facing docs.

The project is currently compatible with Claude Code as the first
shell-capable host. It should not be described as "a Claude Code agent"
as if the host were the product. The product boundary is the local
runtime: CLI, SQLite state, deterministic projectors, domain skills,
capability annotations, human gates, and audit/provenance surfaces.

Updated docs now use "shell-capable agent" or "host agent" where the
sentence is about the general product shape, and reserve Claude Code for
the current compatibility surface.

### F-DOC-03. Current Truth Was Mixed With Historical Provenance

**Severity:** high
**Status:** partially fixed; structural work remains.

The repo has a valuable habit of preserving audit prompts, responses,
release proofs, and plan deltas. The failure mode is that readers land
on a frozen plan and mistake it for the current checklist. Examples
included v0.1.15 being described as pre-implementation after it had
already shipped, v0.1.15.1 hotfix docs still carrying pre-ship labels, and
planning indexes implying older post-cycle directories were active.

This pass added or tightened current-vs-provenance labels in the main
indexes and v0.1.15/v0.1.15.1 entry points. The remaining risk is the
large tactical and strategic docs: they still mix roadmap, history,
triage, and future-cycle material in documents that are too long to be
safe as first-read orientation.

### F-DOC-04. Operator Docs Did Not Match The Actual Runtime Surface

**Severity:** high
**Status:** fixed for the most visible drift.

The root and reporting docs had several stale runtime facts: schema head
and migration counts, test counts, CLI aliases, package state, and
X-rule counts. Generated docs had a missing idempotency legend entry for
`yes-with-replace`.

Fixes applied:

- current package posture moved to v0.1.15.1;
- schema references updated to migration 025 where current-facing;
- suite references updated to the v0.1.15.1 release-gate count;
- `hai pull` examples restored to the capability-contract `--date`
  flag while `--as-of` remains the civil-date flag for daily, snapshot,
  synthesize, explain, today, and related read/planning surfaces;
- root X-rule count updated to 11 total;
- generated capability rendering now documents `yes-with-replace`;
- `agent_cli_contract.md` regenerated from the runtime.

### F-DOC-05. Skills Had Contract Drift

**Severity:** high
**Status:** fixed for the audited skills.

Several agent-operable skill docs were behind the implementation:

- `recovery-readiness` mixed proposal generation with follow-up/review
  composition. It now stops at the proposal boundary.
- `reporting` could narrate proposal objects as if they were committed
  recommendations. It now reads `hai today`, `hai explain`, and optional
  review summaries, and explicitly avoids treating proposals as final.
- `intent-router` lacked the newer intent/target surfaces and W57
  cautions, and its routine refresh path included `state reproject`.
  It now separates memory, intent, and target, and treats reproject as a
  rebuild/repair action.
- `merge-human-inputs` and `strength-intake` had allowed-tools drift.
  Their frontmatter now reflects the actual commands they instruct the
  host agent to use.

This matters because skills are not prose-only docs. They are part of
the agent-operable surface.

### F-DOC-06. Launch And Demo Docs Were Stale

**Severity:** medium
**Status:** launch draft partially fixed; demo flow remains a backlog item.

The Show HN draft and launch checklist still reflected older public
package state and command counts. This pass labels the launch draft as a
draft, updates the major facts, and corrects the host-agent framing.

`reporting/docs/archive/cycle_artifacts/demo_flow.md` still deserves a current rewrite. It
should demonstrate the product thesis: start with a clean local state,
pull or seed data, run the daily loop, show gaps/presence, inspect
provenance with `hai explain`, and demonstrate a W57-gated target or
intent change. The current doc is not wrong enough to block this pass,
but it is not yet a strong demo narrative.

### F-DOC-07. Strategic And Tactical Docs Are Too Heavy For First Read

**Severity:** medium
**Status:** not fixed; should be a named docs workstream.

`reporting/plans/strategic_plan_v1.md` and
`reporting/plans/tactical_plan_v0_1_x.md` are useful as decision logs,
but poor as the first place to understand where the project is going.
They are too long, preserve too much historical texture, and require the
reader to know which rows are active.

Recommended shape:

- keep the current files as provenance;
- add `strategic_plan_v2.md` as the concise product strategy;
- split tactical into "next cycle scope" and "historical release ledger";
- keep workstream IDs and links, but do not make future readers parse
  old audit trails to understand current intent.

### F-DOC-08. Eval Docs Lag The New Failure-Mode Framing

**Severity:** medium
**Status:** not fixed; should route to v0.1.16/v0.1.17 planning.

Anthropic's article makes one thing clearer: evals should not only test
data plumbing or command success. They should test personal-guidance
failure modes:

- sycophantic validation under user pushback;
- one-sided-context overconfidence;
- health/finance/legal high-stakes boundary handling;
- partial-day/no-target insufficiency;
- proposal vs committed recommendation confusion;
- refusal and escalation language;
- cross-domain overreach when the state is incomplete.

The current eval docs and harness docs do not yet explain that frame
well. They should be updated when the eval workstreams resume, not
silently patched into a few paragraphs now.

### F-DOC-09. Explain/Provenance Docs Need One Canonical Surface

**Severity:** medium
**Status:** not fixed.

The project has strong provenance primitives (`x_rule_firing`,
recommendation state, projections, `hai explain`), but the explanation
story is split across architecture prose, generated CLI docs, release
reports, and skills. A future docs pass should make one short canonical
doc for:

- what can be explained;
- what cannot be explained yet;
- how `hai explain` relates to `hai today`, `hai review`, and the local
  state DB;
- which provenance fields are stable enough for agents to rely on.

### F-DOC-10. Domain-Extension Docs Duplicate Authority

**Severity:** low/medium
**Status:** not fixed.

The domain-extension guidance is spread across architecture, state
model, skills, tactical plans, and older cycle docs. The current
duplication is survivable, but it will drift as soon as the next domain
or X-rule family lands. The right fix is to designate one canonical
"add or extend a domain" document and make other docs link to it.

## Fixes Applied In This Pass

| Area | Files |
|---|---|
| Product story and root orientation | `README.md`, `ARCHITECTURE.md`, `REPO_MAP.md`, `ROADMAP.md` |
| Reporting docs orientation | `reporting/docs/README.md`, `reporting/docs/tour.md`, `reporting/docs/architecture.md`, `reporting/docs/agent_integration.md`, `reporting/docs/personal_health_agent_positioning.md`, `reporting/docs/privacy.md`, `reporting/docs/backup_and_recovery.md` |
| Launch/current-state docs | `reporting/docs/launch/PUBLISH_CHECKLIST.md`, `reporting/docs/launch/show_hn_draft.md`, `verification/README.md` |
| Planning indexes and closed cycles | `reporting/README.md`, `reporting/plans/README.md`, `reporting/plans/v0_1_15/README.md`, `reporting/plans/v0_1_15_1/RELEASE_PROOF.md`, `reporting/plans/v0_1_15_1/REPORT.md`, `reporting/plans/tactical_plan_v0_1_x.md` |
| Agent-operable skills | `src/health_agent_infra/skills/recovery-readiness/SKILL.md`, `src/health_agent_infra/skills/reporting/SKILL.md`, `src/health_agent_infra/skills/merge-human-inputs/SKILL.md`, `src/health_agent_infra/skills/strength-intake/SKILL.md`, `src/health_agent_infra/skills/intent-router/SKILL.md` |
| Generated CLI contract | `src/health_agent_infra/core/capabilities/render.py`, `reporting/docs/agent_cli_contract.md` |
| Verification docs/tests | `verification/README.md`, `verification/tests/test_state_clean_projection.py` |

## Remaining Backlog

These are intentionally not hidden as "done". They are the right next
docs workstreams if the project wants its documentation to match the
runtime quality.

| Proposed ID | Scope | Destination |
|---|---|---|
| W-DOC-STRAT | Write `strategic_plan_v2.md`: concise product thesis, user, current state, failure modes, next 3 horizons, and non-goals. | v0.1.16 or post-v0.1.15 docs cycle |
| W-DOC-TACTICAL | Split tactical plan into active next-cycle scope vs historical release ledger. | v0.1.16 |
| W-DOC-DEMO | Create a current `reporting/docs/demo_flow.md` around the daily loop, gaps, explainability, and W57-gated changes, using the archived cycle artifact as provenance only. | v0.1.16 |
| W-DOC-EVAL | Update eval docs for personal-guidance failure modes: sycophancy, one-sided framing, overconfidence, high-stakes boundary handling, and proposal/commit confusion. | v0.1.17 if tied to eval implementation |
| W-DOC-EXPLAIN | Create one canonical explain/provenance doc. | v0.1.17 |
| W-DOC-DOMAIN | Consolidate "extend a domain" documentation into one authority surface. | v0.1.17 |

## Recommendation

Keep this pass as a post-v0.1.15 internal-docs cleanup, not a new
runtime release. The docs are now materially better for a reader trying
to understand what Health Agent Infra is and how an agent should operate
it. The remaining work should be handled as a named docs cycle because
it requires restructuring long-lived planning surfaces, not just fixing
stale facts.
