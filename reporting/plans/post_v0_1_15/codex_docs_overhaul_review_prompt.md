# Codex Review — post-v0.1.15 Internal Docs Overhaul

**Round:** 1
**Tier:** doc-only
**Verdict scale:** `DOCS_SHIP` · `DOCS_SHIP_WITH_NOTES` · `DOCS_SHIP_WITH_FIXES`
**Working directory:** `/Users/domcolligan/health_agent_infra` on `main`,
HEAD pre-this-pass = `c86f80b docs: correct README product framing`. The
overhaul is currently in the working tree (uncommitted at audit time, or
in the most recent post-`c86f80b` commit if commit step has run).

You are reviewing whether the post-v0.1.15 internal-docs overhaul is
ready to ship. This is a doc-only pass — no runtime behavior, schema,
CLI surface, or release tag changes.

## 0. Read-orientation provenance

Read these in order before forming a verdict:

1. `reporting/plans/post_v0_1_15/internal_docs_audit.md` — the
   first-pass audit (10 findings, 6 closed in earlier post-v0.1.15
   cleanup commits).
2. `reporting/plans/post_v0_1_15/codex_internal_docs_audit_v2_response.md`
   — Codex's verification of the v2 audit synthesis (19 findings
   confirmed + 4 new).
3. `reporting/plans/post_v0_1_15/docs_overhaul_plan.md` — the working
   plan for this pass.
4. `reporting/plans/post_v0_1_15/docs_overhaul_report.md` — the final
   report from this pass (changes, verification, residuals).
5. The current operating docs themselves (see §1 below).

Then read the diff against `c86f80b`:

```bash
git diff c86f80b -- README.md ARCHITECTURE.md ROADMAP.md AGENTS.md \
    CONTRIBUTING.md reporting/README.md reporting/docs/ \
    reporting/plans/post_v0_1_15/
```

## 1. The product thesis to validate against

Health Agent Infra is the **local plugin/runtime wrapper around a
shell-capable personal-health agent**. The agent stays the
conversational operator. `hai` is the governed tool surface that
declares what commands exist, which substrates each command may
mutate, what each output must validate against, and which authority
the runtime refuses to grant the agent.

Two anti-framings the docs must avoid:

- **"The runtime IS the agent."** False. The runtime wraps the
  agent.
- **"Claude Code is the product boundary."** False. Claude Code is
  the first compatible host. The contract is the local CLI plus
  capabilities manifest.

## 2. Audit questions — please answer each with verdict + evidence

For each question below, return one of `OK` / `NIT` / `FIX-NEEDED` and
cite file:line. End with an overall verdict at §10.

### Q1 — Wrapper framing

Do `README.md`, `ARCHITECTURE.md`, `reporting/docs/README.md`,
`reporting/docs/architecture.md`,
`reporting/docs/personal_health_agent_positioning.md`, and
`reporting/docs/host_agent_contract.md` consistently describe the
project as a wrapper *around* an agent rather than the agent itself?
Note any drift back to "the agent" framing or any spot where the
wrapper boundary blurs.

### Q2 — Architecture diagrams

Diagrams added or upgraded in this pass:

| ID | File | Type |
|---|---|---|
| README hero | `README.md` "Product boundary" | Mermaid `flowchart LR` |
| Agent-wrapper model | `reporting/docs/architecture.md` | Mermaid `flowchart TB` |
| Agent journey | `reporting/docs/architecture.md` | Mermaid `sequenceDiagram` |
| Runtime pipeline | `reporting/docs/architecture.md` | Mermaid `flowchart TB` |
| Mutation substrate map | `reporting/docs/architecture.md` "Command contract and mutation substrates" | Mermaid `flowchart LR` |
| Three-state audit chain | `ARCHITECTURE.md` (also at `reporting/docs/explainability.md`) | Mermaid `stateDiagram-v2` |
| Domain-extension wiring | `reporting/docs/how_to_add_a_domain.md` | Mermaid (per `gpt_image_prompts.md`) |

Render each Mermaid block on GitHub or via the
[Mermaid Live Editor](https://mermaid.live/) and confirm: (a) it
renders, (b) labels match the prose, (c) no diagram implies
authority the runtime does not have (cloud services, medical
authority, autonomous treatment, multi-agent orchestration unless
explicitly future). Flag any diagram that adds clutter rather than
signal.

### Q3 — README clarity

Is `README.md`:

- Leading with a tight wrapper-framing one-liner?
- Showing the wrapper diagram before the failure-mode wall?
- Tightening the failure-mode and current-state tables to a
  reasonable length for a cold reader?
- Routing readers by audience via a "Read next" or equivalent
  table that includes `host_agent_contract.md`?
- Avoiding misleading or aspirational claims?

Flag misreadings a cold reader could form. The dense "Where the
product stands" + "The loops this enables" + "Why it is different"
sequence is the most likely bloat point — judge whether it carries
its weight.

### Q4 — Host-agent contract page

`reporting/docs/host_agent_contract.md` is new in this pass. Audit:

- Does it consolidate the host-agent rules without duplicating
  authority that lives in `agent_cli_contract.md`,
  `cli_exit_codes.md`, `glossary.md`, or `AGENTS.md`?
- Are all nine mutation classes described correctly per the actual
  manifest output?
- Is the proposal-gate three-state machine
  (`awaiting_proposals` / `incomplete` / `complete`) explained
  unambiguously?
- Is W57 explained operationally (proposal vs activation gap), not
  just named?
- Does it correctly point to `AGENTS.md` for the *contributing*
  contract while keeping itself the *hosting* contract?

Run the manifest yourself and verify the doc:

```bash
uv run hai capabilities --json | python3 -c "
import json, sys
m = json.load(sys.stdin)
classes = sorted({c.get('mutation','?') for c in m['commands']})
print('mutation classes in manifest:', classes)
print('agent_safe == False count:', sum(1 for c in m['commands'] if not c.get('agent_safe', True)))
print('total commands:', len(m['commands']))
"
```

Cross-check the printed `mutation classes` against the doc's table
in §2. (Note: the field name is `mutation` in the manifest output;
the doc calls this `mutation_class` for clarity. Flag if you find
that confusing.)

### Q5 — Domain reference docs

`reporting/docs/domains/{recovery,running,sleep,stress,strength,nutrition}.md`
were upgraded to a uniform structure. Verify:

- All six docs share: Runtime Surface table → Evidence And Accepted
  State → Classifier Reference → Policy / R-rules → Proposal Actions
  → X-rule Participation → Missingness And V1 Limits → Tests.
- All band/status enums in the Classifier Reference tables match
  the live classifier code in
  `src/health_agent_infra/domains/<d>/classify.py`.
- All R-rule tables match the live policy code in
  `src/health_agent_infra/domains/<d>/policy.py`.
- The X-rule Participation sections match
  `reporting/docs/x_rules.md` and
  `src/health_agent_infra/core/synthesis_policy.py`. Specifically:
  - **X2** targets only **strength** and **recovery** (not running)
    in v1. Confirm both `nutrition.md` and `running.md` reflect
    this.
  - **X7** caps confidence on every domain when
    `garmin_stress_band ∈ {high, very_high}`.
  - **X9** is Phase B and only mutates `action_detail` on
    nutrition.
- Test paths in the "Tests" sections actually exist on disk.

### Q6 — Stale facts

Sweep for stale counts/dates/versions on current operating docs
(exclude `reporting/plans/v0_1_X/` sealed cycle artifacts). Canonical
truth as of v0.1.15.1:

- Package version `0.1.15.1`, schema head `25`, 60 annotated CLI
  commands, **2631 passed, 3 skipped** at release gate, 11 X-rules
  (10 Phase A + 1 Phase B), 14 packaged skills.
- intervals.icu preferred; garmin_live structurally marked
  unreliable; CSV fixture default-deny.
- `recovery.md` slug now belongs to the recovery *domain* reference;
  the disaster-recovery doc is `backup_and_recovery.md`.

Flag any stale count, date, version, or path on a current operating
doc.

### Q7 — Generated CLI contract freshness

Run:

```bash
uv run hai capabilities --markdown > /tmp/agent_cli_contract.regen.md
diff -q reporting/docs/agent_cli_contract.md /tmp/agent_cli_contract.regen.md
```

Expected output: no diff (byte-stable). Flag any drift.

### Q8 — Glossary completeness

`reporting/docs/glossary.md` was expanded. Confirm entries exist
for: `accepted state`, `adapted recommendation`, `agent-native`,
`agent-safe`, `bounded`, `capped_confidence`, `classified_state`,
`coverage_band`, `data_quality_daily`, `deterministic boundary`,
`DomainProposal`, `evidence locator`, `forced_action`,
`governed write path`, `host agent`, `ingest_actor`,
`local governance`, `missingness`, `mutation class`, `partial_day`,
`Phase A`, `Phase B`, `planned recommendation`,
`planned_recommendation`, `policy_result`, `proposal gate`,
`proposal_log`, `R-rule`, `recommendation_log`, `review loop`,
`review outcome`, `source freshness`, `supersession`,
`target_status`, `three-state audit chain`, `USER_INPUT`, `W57`,
`X-rule`. Flag missing entries or definitions that contradict the
canonical surface they cite.

### Q9 — Sealed history not rewritten

Confirm that nothing under `reporting/plans/v0_1_X/` was rewritten
in this pass except `reporting/plans/post_v0_1_15/` (the current
working cycle). Run:

```bash
git diff c86f80b --stat -- 'reporting/plans/v0_1_*/' \
    'reporting/plans/v0_1_*_1/' \
    | grep -v 'post_v0_1_15' | head -20
```

Expected: empty output. Flag any sealed-history modification.

## 3. Verification commands you should run

```bash
# Mechanical doc invariants
uv run pytest verification/tests/test_docs_integrity.py \
    verification/tests/test_doc_freshness_assertions.py -q
# Expected: PASS

# README structure assertions
uv run pytest verification/tests/test_readme_structure.py \
    verification/tests/test_readme_quickstart_smoke.py -q
# Expected: PASS

# Generated CLI contract is fresh and byte-stable
uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md
# Expected: empty diff

# Capabilities + parser regression (only if generator changed; should not have)
uv run pytest verification/tests/test_capabilities.py \
    verification/tests/test_cli_parser_capabilities_regression.py -q
# Expected: PASS

# Full suite
uv run pytest verification/tests -q
# Expected: 2631 passed, 3 skipped

# Markdown link/anchor check
# Repeat the local current-docs link check from docs_overhaul_report.md:
# include root operating docs, reporting/README.md, reporting/docs/**/*.md
# excluding reporting/docs/archive/**, plus reporting/plans/post_v0_1_15/*.md.
# Expected from this pass: no broken links/anchors; 378 checked across 51 docs.
```

## 4. Codex deliverables

Return:

1. Overall verdict from the scale (`DOCS_SHIP` /
   `DOCS_SHIP_WITH_NOTES` / `DOCS_SHIP_WITH_FIXES`).
2. Per-question verdicts (Q1..Q9) with file:line evidence.
3. Concrete fix list for any `FIX-NEEDED` finding (file:line +
   exact replacement text).
4. Concrete note list for any `NIT` finding.
5. A short residual-risk paragraph: what could a v0.1.16 reader
   trip on that this pass did not address?

## 5. Out of scope for this audit

These are deferred by the plan and not failures of this pass:

- `strategic_plan_v2.md` rewrite, tactical-plan split.
- `demo_flow.md` rewrite.
- Eval-doc rewrite for personal-guidance failure modes.
- `AGENTS.md` split.
- Diátaxis directory restructure.
- `llms.txt` for agent ingestion.
- Full 13-section domain-reference template.
- GPT Images bitmap hero illustration.

If you find drift in any of these areas, mention it under residual
risk; do not fail the verdict on it.
