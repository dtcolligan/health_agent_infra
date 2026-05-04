# Internal Docs Overhaul - Final Report

**Date:** 2026-05-04
**Tier:** doc-only; no version bump; no PyPI publish; no tag move
**Pre-pass HEAD:** `c86f80b docs: correct README product framing`
**Verdict:** DOCS_OVERHAUL_READY, pending independent Codex review

## 1. Summary of changes

This pass made the agent-wrapper thesis durable across current operating
docs, improved cold-reader navigation, created a canonical host-agent
operating contract, upgraded all six domain references, added high-value
Mermaid visual aids, and fixed stale facts and links surfaced by the audit.

The framing now repeated across the main docs is:

> Health Agent Infra is the local plugin/runtime wrapper around a
> shell-capable personal-health agent. The agent stays the conversational
> operator. `hai` is the governed tool surface that declares what commands
> exist, which substrates each command may mutate, what each output must
> validate against, and which authority the runtime refuses to grant the
> agent.

The committed diff from `c86f80b` is 32 files changed, 1942 insertions, and
354 deletions. New review/audit artifacts live under
`reporting/plans/post_v0_1_15/`; sealed release artifacts under
`reporting/plans/v0_1_*` were not rewritten.

## 2. Research findings from parallel agents

| Agent | Highest-impact finding | Resulting change |
|---|---|---|
| A - Cold Reader Journey | README explained failure modes before the product boundary was clear; role routing was too scattered. | Added the README product-boundary diagram, tightened status/failure tables, and added role-based "Read next" routing. |
| B - Top OSS Docs Patterns | Strong repos separate landing, concepts, how-to, reference, and generated contracts while keeping a clear reader router. | Kept the flat tree for now but improved `reporting/docs/README.md`, preserved generated `agent_cli_contract.md`, and avoided copying prose. |
| C - Visual Aid Opportunities | Diagrams help most at boundaries: agent-wrapper, command mutation substrates, audit chain, and domain-extension wiring. | Added Mermaid diagrams only where they explain ownership or flow; no bitmap images were added. |
| D - Agent Operability / CLI Contract | A host agent needed one compact operating contract for `agent_safe`, mutation classes, proposal gates, W57, source freshness, and refusal handling. | Added `reporting/docs/host_agent_contract.md` and tightened `reporting/docs/agent_integration.md`. |
| E - Domain Reference Quality | Domain docs needed consistent evidence, accepted-state, classifier, policy, action, X-rule, missingness, v1-limit, and test sections. | Upgraded recovery, running, sleep, stress, strength, and nutrition references with code/test links. |
| F - Stale Facts and Link Integrity | Stale counts, stale hotfix wording, and launch/archive drift remained; active-doc links were otherwise structurally healthy. | Fixed ROADMAP test count, x-rule/eval scenario prose, archive skill count, tactical-plan hotfix wording, and backup/recovery routing. |

External documentation patterns were extracted from these sources, among
others: Django docs
<https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/>,
Kubernetes docs <https://kubernetes.io/docs/>, OpenTelemetry docs
<https://opentelemetry.io/docs/>, FastAPI tutorial
<https://fastapi.tiangolo.com/tutorial/>, Cargo docs
<https://doc.crates.io/contrib/documentation/index.html>, uv docs
<https://docs.astral.sh/uv/>, SQLite docs
<https://www.sqlite.org/docs.html>, GitHub CLI manual
<https://cli.github.com/manual/>, and LangChain documentation guidance
<https://docs.langchain.com/oss/javascript/contributing/documentation>.

## 3. External connectors checked

- **GitHub connector / GitHub CLI:** checked repository CI state. The GitHub
  status API returned no combined statuses for `c86f80b`; `gh run list` showed
  the latest push CI run succeeded, with `test (3.11)`, `test (3.12)`, and
  `build` jobs successful.
- **GitHub releases / tags:** read locally via `git tag --sort=-creatordate`
  (latest tags: `v0.1.15.1`, `v0.1.12.1`, `v0.1.12`, `v0.1.11`, `v0.1.10`,
  ...). Remote `gh release list` / `gh release view` were **not** invoked
  in this pass; no release notes were authored, no tag was moved, and no
  GitHub release was created. The local tag history matches the published-
  versions narrative in `reporting/docs/current_system_state.md`.
- **Web search:** available and used for documentation-structure research.
  Only patterns were used; no prose was copied.
- **Live `hai` CLI:** available and used for `hai capabilities --json` /
  `--markdown` freshness checks.
- **Markdown/link tooling:** local Python link checker was used over current
  docs.
- **Browser rendering:** not used; no Markdown preview server was needed.
- **GPT Images:** route was available, but no bitmap assets were generated.
  Mermaid was the better fit for internal, reviewable docs.

## 4. Files changed

New current docs/artifacts:

| Path | Purpose |
|---|---|
| `reporting/docs/host_agent_contract.md` | Host-agent operating contract |
| `reporting/plans/post_v0_1_15/docs_overhaul_plan.md` | Working plan for this pass |
| `reporting/plans/post_v0_1_15/gpt_image_prompts.md` | Image-generation decision record and optional future prompt |
| `reporting/plans/post_v0_1_15/codex_docs_overhaul_review_prompt.md` | Independent Codex review prompt |
| `reporting/plans/post_v0_1_15/docs_overhaul_report.md` | This report |

Root docs changed: `README.md`, `ARCHITECTURE.md`, `AGENTS.md`,
`CONTRIBUTING.md`, `ROADMAP.md`, and `reporting/README.md`.

Current reporting docs changed: `README.md`, `agent_integration.md`,
`architecture.md`, `current_system_state.md`, `explainability.md`,
`glossary.md`, `how_to_add_a_domain.md`, `non_goals.md`,
`personal_health_agent_positioning.md`, `tour.md`, `x_rules.md`,
`launch/show_hn_draft.md`, `archive/doctrine/README.md`,
`domains/README.md`, and all six domain references.

Planning surface changed: `reporting/plans/tactical_plan_v0_1_x.md`.

## 5. Diagrams added and why

Mermaid was used because these are internal docs where source review matters.
The pass added or upgraded five visual concepts:

| Concept | Target docs | Why it helps |
|---|---|---|
| Product boundary | `README.md` | Shows user -> agent -> `hai` -> local state before a cold reader meets the failure-mode table. |
| Agent-wrapper architecture | `reporting/docs/architecture.md` | Centers the agent as conversational operator and `hai` as governed wrapper. |
| Daily/agent journey and runtime pipeline | `reporting/docs/architecture.md` | Separates product perspective from implementation pipeline. |
| Command/mutation substrate map | `reporting/docs/architecture.md` | Makes the nine mutation classes and their local substrates inspectable. |
| Audit/domain extension maps | `ARCHITECTURE.md`, `reporting/docs/explainability.md`, `reporting/docs/how_to_add_a_domain.md` | Shows three-state provenance and the file/code blast radius for adding a domain. |

Existing Mermaid in `reporting/docs/agent_integration.md` and
`reporting/docs/memory_model.md` was left in place rather than duplicated.

## 6. GPT Images prompts created

`reporting/plans/post_v0_1_15/gpt_image_prompts.md` records that no generated
bitmap images were added. It includes one optional future public-asset prompt
for a website/launch page, with explicit exclusions for medical authority,
cloud services, autonomous treatment, and multi-agent orchestration.

## 7. Verification results

```bash
$ git diff --check
# no whitespace errors

$ uv run pytest verification/tests/test_docs_integrity.py \
      verification/tests/test_doc_freshness_assertions.py -q
..s...                                                                   [100%]
5 passed, 1 skipped in 0.69s

$ uv run pytest verification/tests/test_readme_structure.py \
      verification/tests/test_readme_quickstart_smoke.py -q
........                                                                 [100%]
8 passed in 3.02s

$ uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md
# no diff

$ uv run pytest verification/tests/test_capabilities.py \
      verification/tests/test_cli_parser_capabilities_regression.py -q
......................                                                   [100%]
22 passed in 1.65s

$ uv run pytest verification/tests -q
2631 passed, 3 skipped in 123.05s (0:02:03)
```

Markdown link check:

```text
checked 378 markdown links/anchors across 51 current docs; excluded
reporting/docs/archive/** and historical reporting/plans/v0_*
```

The exclusion is intentional: archived doctrine/cycle artifacts are
provenance, not current operating docs.

## 8. Known residual issues

| Item | Why deferred |
|---|---|
| Strategic/tactical plan restructuring | Larger planning-doc cleanup; not needed for this operating-doc pass. |
| `demo_flow.md` rewrite | Depends on v0.1.16 demo/user-session findings. |
| Eval-doc rewrite for personal-guidance failure modes | Tied to planned harness work. |
| Split `AGENTS.md` into coding-agent vs host-agent docs | `host_agent_contract.md` now covers hosting; a deeper split can wait until another host integration earns it. |
| Diataxis directory restructure | Helpful later, but disruptive for a one-maintainer flat tree today. |
| `llms.txt` / agent-ingestion index | Useful future work; outside this pass. |
| Bitmap public hero image | Internal docs are better served by Mermaid. |

The only remaining worktree item after commit is the pre-existing untracked
`reporting/plans/post_v0_1_14/anthropic_personal_guidance_report.md`, which
was deliberately left out.

## 9. What Codex should review

Use `reporting/plans/post_v0_1_15/codex_docs_overhaul_review_prompt.md`.
It asks for:

1. Verdict: `DOCS_SHIP`, `DOCS_SHIP_WITH_NOTES`, or
   `DOCS_SHIP_WITH_FIXES`.
2. Wrapper-framing consistency.
3. Architecture and Mermaid diagram correctness.
4. README clarity and non-misleading status claims.
5. Host-agent contract accuracy.
6. Domain reference accuracy against code/tests.
7. Stale fact and link sweep.
8. Generated `agent_cli_contract.md` freshness.
9. Confirmation that sealed historical release artifacts were not rewritten.

## 10. Ready to commit

Yes. The work is coherent, verified, and committed as:

```text
docs: overhaul internal documentation around agent-wrapper architecture
```

No push, tag move, PyPI publish, or GitHub release was performed.

## Appendix A — Per-agent research evidence

The six parallel research agents in §2 produced their findings in-session;
their full transcripts were not persisted as standalone artifacts (the
audit trail decision was that the *changes they justified* belong in the
docs themselves, not as a parallel report dump). For each agent below,
the durable trail is the file:line citation in the change made and the
pre-pass facts those changes were responding to. A future review can
reconstruct each finding from the diff against `c86f80b`.

### Agent A — Cold-reader journey

- Pre-pass evidence: `README.md` opened with a 14-row failure-mode table
  (then-`README.md:29-44`) and a 16-row "Current state" table
  (then-`README.md:94-110`) before the conceptual model was set; the
  audience-routing surface only existed at `reporting/docs/README.md:40-48`.
- Changes that closed the finding: README "Product boundary" Mermaid
  diagram inserted before the failure-mode table (`README.md:22-43` in
  the post-commit tree); failure-mode table trimmed to 7 rows
  (`README.md:74-84`); audience-routing "Read next" table at
  `README.md:422-429` extended to include `host_agent_contract.md`.

### Agent B — Open-source documentation patterns

- Pattern sources fetched: Rust Book, Cargo, Django, FastAPI, Kubernetes,
  uv/Astral, LangChain, OpenTelemetry, SQLite, GitHub CLI, Anthropic
  Claude API / MCP. URLs preserved in the citations block of agent B's
  in-session report.
- Patterns adopted: audience-card landing block (HIGH-applicability;
  closed via README "Read next" + `reporting/docs/README.md` "Read by
  role"); machine-readable contract (HIGH; already present via
  `hai capabilities --json` and the regenerated `agent_cli_contract.md`);
  mental-model "concepts" page pattern (HIGH; closed via the new
  `host_agent_contract.md`).
- Patterns *not* adopted in this pass: `llms.txt`, Diátaxis directory
  restructure, sidebar navigation. Named in §8 residuals.

### Agent C — Visual-aid opportunities

- Pre-pass evidence: zero Mermaid in `README.md` / `ARCHITECTURE.md` /
  `AGENTS.md`; existing Mermaid limited to
  `reporting/docs/architecture.md`, `agent_integration.md`,
  `memory_model.md`, `explainability.md`.
- Changes that closed the finding: D1 mutation-substrate map at
  `reporting/docs/architecture.md` "Command contract and mutation
  substrates" (Mermaid `flowchart LR`); D2 runtime-pipeline diagram at
  `reporting/docs/architecture.md` "Runtime pipeline under the wrapper"
  (Mermaid `flowchart TB`); D3 three-state audit chain lifted into
  `ARCHITECTURE.md` "Three-State Audit Chain" (Mermaid `stateDiagram-v2`).
  Cap of three new diagrams was respected.

### Agent D — Agent-operability

- Pre-pass evidence: 11 gaps clustered around the absence of one
  canonical host-agent contract page; mutation classes documented as a
  bare table in `agent_cli_contract.md:23-35` with no operational prose;
  proposal-gate three-state machine documented only at
  `agent_integration.md:198-205`; USER_INPUT handling scattered across
  `cli_exit_codes.md:13-20` and `agent_integration.md:155-156`.
- Changes that closed the finding: the new
  `reporting/docs/host_agent_contract.md` consolidates manifest
  discovery (§1), nine-class mutation taxonomy with operational prose
  (§2), proposal-gate three-state machine (§3), `agent_safe` and W57
  (§4 + §6), USER_INPUT exit handling (§5), source-freshness rules
  (§7), and a "what the agent must never do" table (§8). Glossary
  expanded with `proposal gate`, `mutation class`, `classified_state`,
  `policy_result`, `proposal_log`, `planned_recommendation`,
  `recommendation_log`.

### Agent E — Domain reference quality

- Pre-pass evidence: `recovery.md` used vague "X1/X6-style" language
  for X-rule participation; `stress.md` mentioned X7 only as
  "contributes"; `running.md` and `nutrition.md` both stated X2 softens
  running (verified wrong against `core/synthesis_policy.py:621`,
  which restricts X2 targets to `("strength", "recovery")`); `sleep.md`
  vaguely said chronic-deprivation forces "an escalation-style sleep
  action" (the live policy at
  `domains/sleep/policy.py:140-161` forces `sleep_debt_repayment_day`).
- Changes that closed the finding: all six domain docs moved to a
  uniform 8-section structure (Runtime Surface · Evidence And Accepted
  State · Classifier Reference · Policy / R-rules · Proposal Actions ·
  X-rule Participation · Missingness And V1 Limits · Tests). X2
  participation now explicitly says "Running is intentionally not an X2
  target in v1" in `nutrition.md` and `running.md`. Sleep
  chronic-deprivation now names the forced action explicitly. Recovery
  and Stress sections now enumerate every X-rule that targets them.

### Agent F — Stale facts and link integrity

- Pre-pass evidence: 1 high-severity finding (`ROADMAP.md:34` "2630
  passed" vs canonical 2631 at `current_system_state.md:18`); link
  integrity otherwise clean across 51 current docs.
- Changes that closed the finding: `ROADMAP.md:34` corrected to
  `2631 passed, 3 skipped (+50 vs v0.1.14.1)`. The two low housekeeping
  items (personal-path mention in `AGENTS.md:20-22`, archive-perimeter
  wording in `reporting/docs/README.md`) were intentionally not changed
  — see §8 residuals.

### Note on transcript persistence

The agent transcripts themselves were in-session only and were not
written to disk as `agent_a_report.md` / `agent_b_report.md` / etc. The
trade-off was that persisting six raw transcripts would have created
parallel-truth surfaces that drift away from the actual changes. The
audit-trail anchor is therefore: this appendix + the diff against
`c86f80b`. Future cycles that want fuller transcripts can wire the
parallel-agent prompts to a per-cycle artifacts directory before the
session starts.
