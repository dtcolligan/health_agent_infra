# Contributing

Thanks for looking at Health Agent Infra.

## Mental model

The project has two surfaces. Everything you contribute lands in one of them:

- **Python runtime** under `src/health_agent_infra/` — deterministic
  data acquisition, projection, classification, policy, synthesis,
  validation, review, and persistence.
- **Markdown skills** under `src/health_agent_infra/skills/` — the
  agent's judgment layer: rationale, uncertainty surfacing, and
  clarification during narration.

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
4. Add deterministic tests under `safety/tests/`.
5. If the change crosses a schema boundary, update the producing and
   consuming paths in the same commit.

Never:
- Import from `skills/` inside Python runtime code.
- Put rationale prose generation in Python when the action is already
  fixed.
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

1. `uv run pytest safety/tests -q`
2. If you touched packaging or versioning: `uv run python -m build --wheel --sdist`
3. If you touched docs: make sure `README.md`, `CHANGELOG.md`,
   `ROADMAP.md`, `AUDIT.md`, and the active docs under `reporting/docs/`
   still agree.
4. If you touched a skill: verify the corresponding skill-boundary
   tests still pass.
5. If you touched a migration/projector/schema: verify the relevant
   state tests and reproject tests.

## Good first changes

- Strengthen a contract test in `safety/tests/` for malformed proposal
  or recommendation JSON.
- Add eval scenarios or rubric coverage under `safety/evals/`.
- Improve a domain classifier/policy test at a boundary condition.
- Fix active docs that drift from shipped runtime behavior.

## Not in scope

- Web/mobile UI, dashboard, or frontend work.
- Hosted multi-user features.
- Meal-level nutrition / food taxonomy in v1.
- A learning loop / ML calibration of confidence.
- New wearable sources unless the product scope changes intentionally.

## If you're not sure

Start with these:

- `README.md`
- `REPO_MAP.md` — one-page orientation of every top-level entry
- `ROADMAP.md`
- `AUDIT.md`
- `reporting/docs/architecture.md`
- `reporting/docs/non_goals.md`
- `reporting/docs/tour.md`
