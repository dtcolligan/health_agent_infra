# Contributing

## Read First

- [`PAPER.md`](PAPER.md) — what we're shipping, scope, active decisions
- [`AGENTS.md`](AGENTS.md) — operating contract, code-vs-skill boundary,
  CLI boundaries, governance invariants, do-not-do list

This repo exists to ship one artifact: an arXiv preprint by 2026-09-30
with GovernedAgentBench v1.0 released alongside. HAI is frozen as a
product. Do not propose HAI v0.2.1+ work, new domains, new wearable
sources, or user-product breadth.

## Where Contributions Land

| Surface | Path |
|---|---|
| Runtime contract code (frozen except for `WP-RUNTIME-FIX-NNN`) | `hai/src/health_agent_infra/` |
| Markdown skills | `hai/src/health_agent_infra/skills/` |
| Benchmark code | `benchmark/governed_agent_bench/` |
| Benchmark tests | `benchmark/verification/tests/` |
| HAI tests | `hai/verification/tests/` |
| Paper draft | `paper/DRAFT.md` (LaTeX when writing-stage) |

Invariant: **skills never mutate actions; code never improvises
coaching prose.** Skills consume `classified_state` and `policy_result`
as source of truth and do not recompute bands, scores, R-rules, or
X-rules.

## Adding Runtime Code

1. Decide owner: `core/` for cross-domain, `domains/<d>/` for
   domain-specific deterministic logic.
2. Add typed functions/classes; no hidden state.
3. Wire a CLI surface in `hai/src/health_agent_infra/cli/` only if
   genuinely needed.
4. Add deterministic tests under `hai/verification/tests/`.
5. Cross-schema changes update producing and consuming paths in the
   same commit.

Never import from `skills/` inside Python runtime code.

## Adding a Skill

1. Edit `hai/src/health_agent_infra/skills/<skill-name>/SKILL.md` or
   create a new skill directory.
2. Keep frontmatter valid (`name`, `description`, `allowed-tools`,
   `disable-model-invocation`).
3. Scope `allowed-tools` tightly.
4. Add or update skill-boundary tests so deterministic logic cannot
   drift back into markdown.

Never re-implement classification, thresholds, or R/X-rule logic in a
skill. Never tell the agent to mutate runtime-owned fields from
markdown.

## Before Opening a PR

1. `uv run pytest hai/verification/tests -q`
2. `uv run pytest benchmark/verification/tests -q`
3. If packaging changed: `uvx --from build python -m build --wheel --sdist`
4. If docs changed: confirm `README.md`, `PAPER.md`, `AGENTS.md`,
   `CLAUDE.md`, and the lane READMEs still agree.
5. If a skill changed: skill-boundary tests still pass.
6. If a migration/projector/schema changed: state tests and reproject
   tests pass.

## Not In Scope

- Web/mobile UI, dashboard, frontend.
- Hosted multi-user features.
- Meal-level nutrition / food taxonomy.
- Learning loop / ML calibration of confidence.
- New wearable sources.
- Consumer-product polish not supporting the preprint, benchmark, or
  reference-runtime contract.
- New cold-start planning files. Decisions update in place in
  `PAPER.md`; provenance goes to `ARCHIVE/`.

## If You're Not Sure

Start with [`PAPER.md`](PAPER.md) and [`AGENTS.md`](AGENTS.md). If
still unclear, ask Dom rather than guessing.
