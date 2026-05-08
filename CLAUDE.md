@AGENTS.md

This file is the Claude-Code-specific operational layer on top of the
universal contract in `AGENTS.md`. Everything in `AGENTS.md` applies;
this file adds the patterns, commands, and signposts that make a fresh
Claude session efficient.

## Claude Code Specifics

- This is the maintainer's daily-driver loop. Skills under
  `src/health_agent_infra/skills/` are also user-installed at
  `~/.claude/skills/` via `hai setup-skills`. Edit the packaged copy,
  not the installed copy.
- Path-scoped rules live in `.claude/rules/` when present.
- For mutating CLI calls during a session, prefer plan mode first.
- The `intent-router` skill is the authoritative natural-language-to-`hai`
  mapper; invoke it rather than composing mutation commands from intuition.

## Session-start orientation

When opening a fresh session, read in this order:

1. **`PROJECT_FRAME.md`** — current research framing and priority order.
2. **`PROJECT_DECISIONS.md`** — post-reframe decision log and locked
   project choices.
3. **`PROJECT_OPERATING_MODEL.md`** — internal operating model and
   documentation-alignment gate.
4. **`AGENTS.md`** — the operating contract (governance invariants, settled
   decisions D1-D18, architectural seams, "Do Not Do").
5. **`HYPOTHESES.md`** — current research hypotheses.
6. **`research/runtime_contracts_paper/PAPER_FRAME.md`** — locked paper /
   benchmark framing.
7. **`research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`** —
   model/baseline/ablation evaluation strategy.
8. **`benchmarks/governed_agent_bench/README.md`** — benchmark scope.
9. **`README.md`** — research-facing repo overview.
10. **`docs/hai/hai_reference_runtime.md`** if you need HAI install,
   operator workflow, domains, or CLI surface.
11. **`ARCHITECTURE.md`** + **`REPO_MAP.md`** if you need to find something.
12. **`reporting/plans/README.md`** only when you need HAI release history or
   a specific HAI runtime cycle plan.

For a "what just shipped" question, read
`reporting/plans/v0_1_X/RELEASE_PROOF.md` for the most recent X.

## Common commands

```bash
# Test suite (full)
uv run pytest verification/tests -q

# Targeted test file
uv run pytest verification/tests/test_<area>.py -q

# Type-check (uses uvx because the project venv lacks mypy)
uvx mypy src/health_agent_infra

# Security scan
uvx bandit -ll -r src/health_agent_infra

# Build wheel + sdist (uses uvx because the project venv lacks build)
uvx --from build python -m build --wheel --sdist

# CLI surface checks
uv run hai capabilities --json
uv run hai capabilities --markdown > docs/hai/agent_cli_contract.md
uv run hai doctor

# Persona matrix (13 personas, ~5 min; P13 is matrix-only — added
# v0.1.14 W-EXPLAIN-UX as a low-domain-knowledge maintainer-substitute
# reader for `hai explain` confusion review)
uv run python -m verification.dogfood.runner /tmp/persona_run

# Warning gates (broader gate restored at v0.1.13 W-N-broader; clean
# through v0.1.14.1 ship-time)
uv run pytest verification/tests \
    -W error::pytest.PytestUnraisableExceptionWarning -q   # narrow (v0.1.11+)
uv run pytest verification/tests -W error::Warning -q      # broader (v0.1.13+)
```

The project venv intentionally does not bundle `mypy`, `bandit`, or
`build`. Use `uvx` for one-shot tool invocations to avoid mutating
`uv.lock`.

## Cycle pattern signposts

A release cycle produces the following files under
`reporting/plans/v0_1_X/`:

| Phase | Files |
|---|---|
| Scope | `PLAN.md`, `CARRY_OVER.md` (when present) |
| D14 plan-audit | `codex_plan_audit_prompt.md` → `codex_plan_audit_response*.md` (rounds 1-N) + `_response_response.md` companions |
| Phase 0 (D11) | `audit_findings.md` |
| Governance | `cycle_proposals/CP{1..N}.md` |
| Implementation review | `codex_implementation_review_prompt.md` → `_response*.md` (rounds 1-N) + `_response_response.md` companions |
| Ship | `RELEASE_PROOF.md`, `REPORT.md` |

**Empirical settling shapes (twice-validated):**

- **D14 plan-audit:** 4 rounds, 10 → 5 → 3 → 0 findings. Budget 2-4 rounds
  for substantive PLANs, single round for hardening/doc-only.
- **Implementation review:** 3 rounds, 5 → 2 → 1-nit. Budget 2-3 rounds.

If round N has *more* findings than round N-1, the previous response
introduced second-order issues — re-read your own diff.

## Patterns the cycles have validated

The universal-AI-agent patterns (provenance discipline, summary-
surface sweep on partial closure, honest partial-closure naming,
audit-chain empirical settling shape) live in **AGENTS.md**
"Patterns the cycles have validated" since they apply to Codex
too. Read those when authoring or revising any artifact in a
cycle directory. CLAUDE.md does not duplicate them.

## Local state vs git state

- **State inspection surfaces:** `hai today`, `hai explain`, `hai doctor`,
  `hai stats`. Use these, not raw `sqlite3 state.db`.
- **Mutations:** `hai propose` / `hai synthesize` / `hai review record` /
  `hai intake {readiness,nutrition,stress,gym,note}` / `hai intent commit` /
  `hai target commit`. The agent never writes to `state.db` directly.
- **Settings / personal data:** never assume body composition, training
  history, or daily macro targets. Ask, pull from existing state, or
  refuse the personalised claim. (See user-memory file
  `feedback_never_assume_personal_data.md` if available.)

## Plan-mode triggers

Use plan mode (or at minimum surface the plan in chat first) when:

- Authoring a `PLAN.md` for a new cycle.
- Drafting a Codex audit prompt.
- Editing `AGENTS.md` "Settled Decisions" or "Do Not Do" — these are
  load-bearing, not editorial.
- Applying a CP delta to AGENTS.md / strategic plan / tactical plan
  during cycle work.
- Any `cli.py` change beyond a single help-text edit (cli.py is at
  ~10k lines and a misplaced parser-arg can break the capabilities
  manifest contract).
- A test surface that exceeds 1-2 new test files (the suite has
  documented assumptions about test isolation; large additions need
  a sanity check).

For doc-only edits, smaller code fixes (mypy class, single-domain
policy.py update), and CLI help-text tweaks: just execute.

## Release toolchain quick reference

Per the user-memory `reference_release_toolchain.md`:

```bash
# Build (project venv lacks `build`)
uvx --from build python -m build --wheel --sdist

# Smoke-test wheel locally before PyPI
uv run pip install --force-reinstall \
    dist/health_agent_infra-<v>-py3-none-any.whl
uv run hai capabilities --json | \
    uv run python -c "import json,sys; print(json.load(sys.stdin)['hai_version'])"

# Upload to PyPI (~/.pypirc holds the token)
uvx twine upload \
    dist/health_agent_infra-<v>-py3-none-any.whl \
    dist/health_agent_infra-<v>.tar.gz

# Verify install — bypass CDN cache (~2 min lag is normal)
pipx install --force \
    --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" \
    'health-agent-infra==<v>'
```

The harness blocks direct `git push` to `main`. Have the maintainer
push (`! git push origin main`) or open a PR via `gh pr create`.

## What lives in AGENTS.md vs CLAUDE.md

| AGENTS.md (universal) | CLAUDE.md (this file) |
|---|---|
| Project description, research reframe, code-vs-skill boundary, CLI boundaries, six domains, governance invariants, settled decisions, architectural seams, "Do Not Do" | Session-start orientation, common commands, cycle-pattern signposts, audit empirical settling shapes, partial-closure naming convention, plan-mode triggers, release toolchain |

If a contract decision applies to all AI agents (Codex, Claude, etc.),
it goes in AGENTS.md. If it's a Claude-Code session-efficiency
pattern, it goes here. The `@AGENTS.md` import at the top of this file
keeps both surfaces visible to Claude on session start.
