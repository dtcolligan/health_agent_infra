# Internal Docs Overhaul Plan

Status: working implementation plan for the post-v0.1.15 internal docs pass.
This is a doc-only pass; it must not change runtime behavior, publish, push,
retag, or rewrite sealed release artifacts.

## Current Diagnosis

The repo has strong proof material but still makes a cold reader assemble too
much context. The current docs already contain the correct core framing in
several places: Health Agent Infra is the local plugin/runtime wrapper around
a shell-capable personal-health agent. The agent remains the conversational
operator; `hai` is the governed tool surface.

Main gaps:

- Reader routing is uneven across README, docs index, tour, repo map, and
  current-system-state docs.
- Architecture is correctly shifting to the agent-wrapper view, but needs that
  view to remain primary and the internal pipeline to remain secondary.
- Agent integration needs sharper host-agent rules for W57, source freshness,
  fixture/live separation, refusals, retries, and review IDs.
- Six domain docs exist but need reference-grade band/action/rule/missingness
  details and test links.
- A few active docs carry stale counts or stale future/hotfix wording.

## Workstreams

1. **Reader journey and navigation**
   - Tighten README product frame, quickstart, current/proven status,
     command summary, non-goals, and role-based read-next links.
   - Improve `reporting/docs/README.md`, `reporting/README.md`, and
     `tour.md` routing without reorganizing the tree.

2. **Architecture and agent-operability**
   - Preserve and improve the uncommitted wrapper-framing rewrite in
     `ARCHITECTURE.md` and `reporting/docs/architecture.md`.
   - Add small, diffable Mermaid diagrams for product boundary, agent journey,
     runtime pipeline, explainability, and domain-extension wiring.
   - Expand `agent_integration.md` with minimum loop sequencing, W57 commit
     gates, source-safety rules, and refusal/retry handling.

3. **Domain references**
   - Upgrade `reporting/docs/domains/{recovery,running,sleep,stress,strength,nutrition}.md`
     with evidence inputs, accepted state, classifier band values, policy
     result shape, R-rules, proposal actions, X-rule participation,
     missingness, v1 limits, and test links.
   - Fix verified domain drift: X2 does not target running; sleep chronic
     deprivation forces `sleep_debt_repayment_day`; absent recovery soreness
     currently causes insufficient coverage.

4. **Glossary and stale fact cleanup**
   - Expand `reporting/docs/glossary.md` for mutation class, proposal gate,
     governed write path, partial day, source freshness, review outcome, and
     the three-state audit chain.
   - Sweep active docs for stale scenario counts, current-vs-provenance
     routing, old hotfix language, and stale launch/archive landing text.

5. **Audit trail**
   - Write `gpt_image_prompts.md` documenting why no generated bitmap assets
     were used and preserving an optional future public-asset prompt.
   - Write `codex_docs_overhaul_review_prompt.md`.
   - Write `docs_overhaul_report.md`.

## Files To Edit

Primary docs:

- `README.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `CONTRIBUTING.md`
- `reporting/README.md`
- `reporting/docs/README.md`
- `reporting/docs/current_system_state.md`
- `reporting/docs/architecture.md`
- `reporting/docs/host_agent_contract.md`
- `reporting/docs/agent_integration.md`
- `reporting/docs/explainability.md`
- `reporting/docs/glossary.md`
- `reporting/docs/tour.md`
- `reporting/docs/x_rules.md`
- `reporting/docs/non_goals.md`
- `reporting/docs/how_to_add_a_domain.md`
- `reporting/docs/domains/*.md`

Secondary current navigation/provenance surfaces:

- `reporting/docs/archive/doctrine/README.md`
- `reporting/docs/launch/show_hn_draft.md`
- `reporting/plans/tactical_plan_v0_1_x.md`

New artifacts:

- `reporting/plans/post_v0_1_15/gpt_image_prompts.md`
- `reporting/plans/post_v0_1_15/codex_docs_overhaul_review_prompt.md`
- `reporting/plans/post_v0_1_15/docs_overhaul_report.md`

## Docs Intentionally Not Touched

- Historical release proofs, audit responses, and sealed cycle artifacts under
  `reporting/plans/v0_*/` unless they are active navigation surfaces named
  above.
- The stale checkout under `/Users/domcolligan/Documents/health_agent_infra/`.
- Generated `reporting/docs/agent_cli_contract.md` unless a live generation
  check shows drift.
- Runtime code, migrations, tests, and packaged skills.

## External Connectors And Tools

- GitHub connector was available for commit status/jobs. It returned no
  PR-only workflow runs for the current commit; `gh run list` showed the latest
  push CI for `c86f80b` succeeded, and the GitHub jobs endpoint showed 3.11,
  3.12, and build jobs successful.
- Web browsing was available and used for documentation-pattern examples
  (Django, Kubernetes, uv/Astral, GitHub CLI). Patterns only are used; prose is
  not copied.
- Browser rendering was not needed because the docs are Markdown and diagrams
  are Mermaid source.
- GPT Images route is available, but bitmap diagrams are not useful for this
  internal pass.

## Risks

- Overcorrecting into a tree restructure would make review harder than the
  docs problem warrants. This pass improves routing in place.
- Domain docs can drift if they list too much implementation detail. The fix is
  to cite code/tests and state exact v1 limits rather than duplicating all
  thresholds.
- Diagrams can imply authority the runtime does not have. Every diagram must
  show the agent as operator and `hai` as governed wrapper, not a cloud
  service, medical authority, or autonomous treatment planner.
- Active-vs-historical edits must not rewrite sealed release history.

## Verification Commands

```bash
git diff --check
uv run pytest verification/tests/test_docs_integrity.py verification/tests/test_doc_freshness_assertions.py -q
uv run pytest verification/tests/test_readme_structure.py verification/tests/test_readme_quickstart_smoke.py -q
uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md
```

Markdown link check: run a local checker over active docs and exclude frozen
historical cycle artifacts unless they are current landing pages.

If generated CLI contract changes unexpectedly:

```bash
uv run pytest verification/tests/test_capabilities.py verification/tests/test_cli_parser_capabilities_regression.py -q
```

## Codex Review Plan

The review prompt will ask a fresh Codex pass to audit product framing,
architecture diagram correctness, README clarity, visual aid usefulness,
agent-operability, domain accuracy, stale links/facts, generated-doc freshness,
and whether historical artifacts were inappropriately rewritten.

Verdicts: `DOCS_SHIP`, `DOCS_SHIP_WITH_NOTES`, `DOCS_SHIP_WITH_FIXES`.
