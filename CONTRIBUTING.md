# Contributing

## Mental model

This repo is a runtime-contract research project with HAI as the first
reference runtime and GovernedAgentBench as the benchmark artifact.
Read [`PROJECT_FRAME.md`](PROJECT_FRAME.md) before assuming HAI product
polish is the next priority. Read
[`PROJECT_OPERATING_MODEL.md`](PROJECT_OPERATING_MODEL.md) before changing
project direction, benchmark scope, or paper-facing claims.

Most HAI contributions land in one of two implementation surfaces:

- **Python runtime** under `src/health_agent_infra/` — deterministic
  data acquisition, projection, classification, policy, synthesis,
  validation, review, and persistence.
- **Markdown skills** under `src/health_agent_infra/skills/` — the
  agent's judgment layer: rationale, uncertainty surfacing, and
  clarification during narration.

Research and benchmark contributions land under:

- **GovernedAgentBench** under `benchmarks/governed_agent_bench/` —
  task schemas, frozen manifests, trajectories, scorer logic, baselines,
  and reports.
- **Paper artifacts** under `research/runtime_contracts_paper/` —
  framing, experiment plans, and reproducibility docs.

The rebuild's central rule is simple:

- If it is deterministic, testable, and should never vary by model
  mood, it belongs in Python.
- If it is judgment about phrasing, ambiguity handling, or how to
  explain an already-constrained action, it belongs in a skill.

## How to add runtime code

1. Decide which package owns it:
   - `core/` for cross-domain mechanics (`state`, `pull`, `clean`,
     `synthesis`, `writeback`, `review`, `config`)
   - `domains/<domain>/` for domain-specific deterministic logic
     (`schemas.py`, `classify.py`, `policy.py`, optional
     `signals.py`/`intake.py`)
2. Add typed functions/classes. No hidden state, no silent global
   mutation.
3. Wire a CLI surface in `src/health_agent_infra/cli.py` only if the
   agent or operator genuinely needs it.
4. Add deterministic tests under `verification/tests/`.
5. If the change crosses a schema boundary, update the producing and
   consuming paths in the same commit.

Never:
- Import from `skills/` inside Python runtime code.
- Put free-form rationale prose generation in Python when the action is
  already fixed.
- Break the local-state invariant: the SQLite state DB is the source of
  truth, not chat memory.

## How to add or edit a skill

1. Edit the existing packaged skill under
   `src/health_agent_infra/skills/<skill-name>/SKILL.md`, or create a
   new skill directory there if the new surface is real.
2. Keep frontmatter valid (`name`, `description`, `allowed-tools`,
   `disable-model-invocation`).
3. Keep the skill bounded: it should consume `classified_state` and
   `policy_result` as source of truth, not redo arithmetic or rules.
4. Scope `allowed-tools` tightly.
5. Add or update the matching skill-boundary tests so deterministic
   logic cannot drift back into markdown.

Never:
- Re-implement classification, thresholds, or X-rule/R-rule logic in a
  skill.
- Tell the agent to mutate runtime-owned fields (`action`,
  `daily_plan_id`, etc.) from markdown.
- Use diagnosis-shaped language in recommendations or rationales.

## Before opening a PR

1. `uv run pytest verification/tests -q`
2. If you touched packaging or versioning: `uv run python -m build --wheel --sdist`
3. If you touched docs: make sure `README.md`, `CHANGELOG.md`,
   `PROJECT_FRAME.md`, `PROJECT_OPERATING_MODEL.md`, `HYPOTHESES.md`,
   `ROADMAP.md`, `AUDIT.md`,
   `research/runtime_contracts_paper/PAPER_FRAME.md`,
   `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`, and the
   active HAI docs under `docs/hai/` still agree.
4. If you touched a skill: verify the corresponding skill-boundary
   tests still pass.
5. If you touched a migration/projector/schema: verify the relevant
   state tests and reproject tests.

## Good first changes

- Strengthen a contract test in `verification/tests/` for malformed proposal
  or recommendation JSON.
- Add eval scenarios or rubric coverage under `verification/evals/`.
- Add GovernedAgentBench pilot tasks, recorded trajectories, or scorer
  checks under `benchmarks/governed_agent_bench/`.
- Improve a domain classifier/policy test at a boundary condition.
- Fix active docs that drift from shipped runtime behavior.

## Not in scope

- Web/mobile UI, dashboard, or frontend work.
- Hosted multi-user features.
- Meal-level nutrition / food taxonomy in v1.
- A learning loop / ML calibration of confidence.
- New wearable sources unless the product scope changes intentionally.
- Consumer-product polish that does not support the paper, benchmark, or
  reference-runtime contract.

## If you're not sure

Start with these:

- `PROJECT_FRAME.md`
- `PROJECT_OPERATING_MODEL.md`
- `HYPOTHESES.md`
- `README.md`
- `REPO_MAP.md` — one-page orientation of every top-level entry
- `ROADMAP.md`
- `research/runtime_contracts_paper/PAPER_FRAME.md`
- `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`
- `benchmarks/governed_agent_bench/README.md`
- `AUDIT.md`
- `docs/hai/architecture.md`
- `docs/hai/non_goals.md`
- `docs/hai/tour.md`
