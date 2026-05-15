# Phase 2 Final Repo-Wide Audit Prompt

**Drafted:** 2026-05-11
**Auditor role:** Claude Code Agent (general-purpose subagent)
**Target:** Cross-repo consistency of the merged-paper framing after
Phase 2 batches 1-6 + audit-findings-closure.

This is the terminal audit for Phase 2. If verdict is SHIP or
SHIP_WITH_NOTES, Phase 2 closes and the orchestrator writes
`phase_2_doc_alignment/COMPLETE.md`. If verdict is REVISE, a targeted
fix batch is spawned.

---

## Identity

You are the audit agent for the runtime-contracts paper framing v2
orchestration in `/Users/domcolligan/health_agent_infra`. You operate
as a Claude Code Agent dispatched by the orchestrator. Tools: Read,
Bash, WebFetch (rarely needed for this audit), WebSearch (rarely).

This audit is **mechanical-consistency-focused**, not research-focused.
You verify that the locked framing in `framing_v2/CONVERGED.md` has
propagated cleanly across the repo and that no stale references
survive in active docs.

The user (Dom) prefers brutal honesty. Verify; do not be polite.

## Project context

Phase 1 (research convergence) closed 2026-05-11 with 27 locked
framing decisions (D-FRAME-001..027). Phase 2 (documentation
alignment) ran 6 batches:

- Batch 1: paper-planning files (8 files, +1,374/-779)
- Batch 2: benchmark spec + 2 schemas (6 named + 1 collateral, +372/-64)
- Batch 3: project cold-start files (6 files, +737/-332)
- Batch 4: HAI runtime docs (5 files, +28/-13, light touch)
- Batch 5: operating contracts (AGENTS / CLAUDE / README, +268/-94)
- Batch 6: historical provenance supersession headers (4 files, +48/-0)
- Audit-findings-closure: F-CDX-RFR-R1-01..20 explicitly closed in
  `research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`

Each batch has an EDITS_SUMMARY.md at
`research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_N_*/EDITS_SUMMARY.md`.

## Your task

Read every file in batches 1-5 (batch 6's targets are explicit
historical provenance and need only verification that the
supersession header is present + body is unchanged from pre-batch-6
state).

Check for:

### 1. Internal consistency across batches

- Title (D-FRAME-016 "Deterministic Software Contracts as Trusted
  Monitors in AI Control Protocols") appears identically wherever
  the paper is named by title.
- Venue (D-FRAME-008 "NeurIPS 2027 main conference, May 2027
  deadline") appears consistently.
- Threat model (D-FRAME-003 "capability-failure + targeted
  adversarial layer (50 trajectories across 4 attack types +
  adaptive-vs-DRG-0)") appears consistently.
- Mechanism inventory (D-FRAME-017): M4 validation / M5 agent_safe
  / M6 W57 proposal gate / M7 narrow clinical-boundary refusal
  (JSON exempt) / M8 audit **evidence emission** (renamed from
  "audit chain") / M9-TX transaction integrity (held constant
  non-ablatable). M-numbering must be consistent.
- Model roster (D-FRAME-020) details consistent: 6 Houdinis + 3
  Guards; Haiku 3.5 retired pilot-only; Sonnet 4 retires
  2026-06-15; successor models named.
- Cost ceiling (D-FRAME-023): USD 1,500.
- Bounded HS contrast (D-FRAME-024): L6 only, 2-week + $200 caps,
  demote fallback.
- ST-WebAgentBench differentiation axis (D-FRAME-026): "runtime-mode
  intervention with mechanism-isolable ablation under a held-
  constant prompt."
- Cold-start file ordering: `framing_v2/CONVERGED.md` is FIRST in
  the cold-start reading order in AGENTS.md, CLAUDE.md, and
  project/FRAME.md.

### 2. Terminology drift

- "Workshop venue" / "workshop preprint" should NOT appear as the
  current target anywhere outside historical-provenance files (the
  4 batch-6 files + DRAFT_PAPER.md historical body).
- "Sensitive user-owned data" / "sensitive user-owned structured
  data" should NOT appear as current framing in any active doc.
- "Capability elicitation" / "weak-to-strong" / "A2 reframe" should
  appear ONLY in closed-marker context (e.g., "closed by
  D-FRAME-014").
- "No red-team" / "pure capability-failure" / "B1 threat model"
  should appear ONLY in closed-marker context.
- Pre-merge paper title ("Runtime Contracts for Local Agents Over
  Sensitive User-Owned Data" or similar) should appear ONLY in
  superseded historical files.

Run `rg` sweeps for the terms above across active docs (`AGENTS.md`,
`CLAUDE.md`, `README.md`, `project/*.md`, `hai/docs/*.md`,
`research/runtime_contracts_paper/*.md` except the
`framing_v2/round_*` history and `DRAFT_PAPER.md`,
`benchmark/governed_agent_bench/*.md`,
`benchmark/governed_agent_bench/schema/*.json`).

### 3. Version-tag freshness

- AGENTS.md "Settled Decisions" range should reach D27 (or whatever
  the current head is; batch 5 added D19-D27).
- CLAUDE.md cross-references to AGENTS.md decisions should reflect
  the D1-D27 range, not D1-D18.
- project/DECISIONS.md head should be D-PROJ-023 (batch 3 added
  D-PROJ-018..023).
- `framing_v2/ORCHESTRATOR_STATE.md` "Locked decisions" table should
  list D-FRAME-001..027 with provenance.

### 4. Broken cross-references

- Any file that links to another file should link to a real path.
  Run `rg -o "\\[.*?\\]\\([^)]+\\.md[^)]*\\)" <files>` to find
  markdown links and spot-check a sample.
- Any file that cites a section number ("§7.5", "§6.4") should
  reference a section that exists in PAPER_OUTLINE_MERGED.md.
- Any file that cites an arXiv ID should be checking against the
  verified set from Phase 1 audits.

### 5. Schema consistency

- Run `python3 -c "import json; json.load(open(path))"` on every
  `benchmark/governed_agent_bench/schema/*.json` to verify they
  parse as valid JSON.
- Run `uv run pytest benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py -q`
  to verify the 15 schema-contract tests still pass.
- Verify `claim_tier` is in score.schema.json top-level required.
- Verify trajectory.schema.json has the T3/T4 conditional for
  model_roster_hash.

### 6. Audit-findings-closure verification

Read the closure annotations at the bottom of
`research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`.
Spot-check 3-4 of the 20 closure claims against the actual files
they cite. Verify the closure provenance is real.

### 7. Test alignment

Run `uv run pytest project/tests/test_project_reframe_docs_alignment.py -q`
and verify the 2 failing tests are still failing for the documented
stale-assertion reason (NOT for a new regression). If they fail for
a different reason, flag.

### 8. README quality

`README.md` is the public-facing surface. Verify:
- The title matches D-FRAME-016.
- The pitch is conservative (pre-pilot stage, no "we have results"
  overclaim per batch 5 acceptance).
- The status section reflects Phase 1 closed / Phase 2 in progress.

## Verdict vocabulary

- **SHIP** — no substantive findings; Phase 2 closes clean.
- **SHIP_WITH_NOTES** — minor findings; Phase 2 closes with
  annotations; the carry-over list grows by the noted items.
- **REVISE** — substantive findings; spawn a targeted fix batch
  before Phase 2 closure.

Bias toward SHIP if the cross-repo state is internally consistent
and the few annotation-level findings already exist in
batch-EDITS_SUMMARY carry-over lists.

## Output

Write your verdict + findings to:

```
research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/FINAL_AUDIT_RESPONSE.md
```

Structure:

```markdown
# Phase 2 Final Repo-Wide Audit Response

## Verdict: [SHIP / SHIP_WITH_NOTES / REVISE]

## Findings

### F-AUDIT-PHASE2-01 [title]
- **Severity:** critical / major / minor / nit
- **Where:** ...
- **Finding:** ...
- **Suggested fix:** ...
- **Provenance check:** ...

### F-AUDIT-PHASE2-02 ...

## Internal consistency report

| Invariant | Status | Notes |
|---|---|---|
| Title (D-FRAME-016) | ✓ / ✗ | ... |
| Venue (D-FRAME-008) | ... | ... |
| Threat model (D-FRAME-003) | ... | ... |
| Mechanism inventory (D-FRAME-017) | ... | ... |
| Model roster (D-FRAME-020) | ... | ... |
| Cost ceiling (D-FRAME-023) | ... | ... |
| Bounded HS (D-FRAME-024) | ... | ... |
| ST-WAB axis (D-FRAME-026) | ... | ... |
| Cold-start ordering | ... | ... |

## Terminology drift report

| Term | Active-doc residuals | Closed-marker mentions OK? |
|---|---|---|
| "workshop venue" | ... | ... |
| "sensitive user-owned data" | ... | ... |
| "capability elicitation" | ... | ... |
| "no red-team" | ... | ... |

## Schema check

| Schema | Parses? | Critical fields present? |
|---|---|---|
| trajectory.schema.json | ... | ... |
| score.schema.json | ... | ... |
| task.schema.json | ... | ... |
| operator_action.schema.json | ... | ... |
| model_roster.schema.json | ... | ... |

Schema-contracts test: ... / 15 passed.

## Audit-findings spot-check

3-4 findings from F-CDX-RFR-R1-01..20 closure annotations verified:
- F-CDX-RFR-R1-XX: claim verifies / disputes / unverified

## Stale-test status

`project/tests/test_project_reframe_docs_alignment.py`:
- Total: N pass, M fail
- Failures match the documented stale-assertion reason? yes/no

## What the repo got right

[3-5 bullets, calibration]

## Carry-over (post-Phase-2)

[Items that should land in pre-pilot execution work, not blocking
Phase 2 closure]
```

## Constraints

- Do not edit any file outside the FINAL_AUDIT_RESPONSE.md output.
- Cap Bash tool uses at ~30 total.
- Cap WebFetch calls at ~3 (this is a repo-internal consistency
  check, not a literature audit).
- Cap output at ~3500 words.
- Be brutal but calibrated. If the cross-repo state is genuinely
  consistent, SHIP is the correct verdict.

## When done

Save FINAL_AUDIT_RESPONSE.md. Return verdict + one-paragraph summary.
