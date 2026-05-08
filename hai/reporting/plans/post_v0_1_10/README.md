# Post-v0.1.10 — Handover for the Next Session

> **Authored 2026-04-28** at v0.1.10 ship by Claude. Dom is closing
> the current session and opening a fresh one to drive a demo.
> This folder is the handover artifact: read it first if you're a
> Claude session opening cold post-v0.1.10.

---

## What just shipped (v0.1.10)

- **Released to PyPI** as `health-agent-infra==0.1.10` —
  https://pypi.org/project/health-agent-infra/0.1.10/
- **Tagged + pushed** as `v0.1.10` to
  `github.com:dtcolligan/health_agent_infra` on `main`.
- **Three Codex audit rounds** (R1 DO_NOT_SHIP → R2 DO_NOT_SHIP →
  R3 SHIP_WITH_NOTES) closed every in-scope finding.
- **Test surface:** 2202 passed, 2 skipped (was 2133 pre-cycle, +69
  tests). Hermetic across env states (passes regardless of whether
  intervals.icu credentials are configured).
- **Persona harness:** 8 personas, 0 crashes, 3 expected F-C-04
  residuals (deferred to v0.1.11 W-B).

Detail: `reporting/plans/v0_1_10/RELEASE_PROOF.md` and
`reporting/plans/v0_1_10/PLAN.md`.

## What v0.1.10 deliberately deferred

**Release-blocker-class for v0.1.11** (audit-chain integrity is the
v0.1.11 thesis):

- **W-E** — `hai daily` re-run state-change supersession (F-B-02).
- **W-F** — Audit-chain version-counter integrity (F-B-01).

Plus Codex round-1 concerns:

- **W-R** — Running-rollup provenance completeness (F-CDX-IR-05).
- **W-S** — Persona harness drift guards (F-CDX-IR-06).
- **W-T** — In-memory threshold injection seam audit (F-CDX-IR-R3-N1).

Full v0.1.11 plan: `reporting/plans/v0_1_11/PLAN.md`.

## The strategic + tactical planning tree (Phase 4 work)

Authored alongside v0.1.10 in the same session. **Already on main.**
Has not yet received its own Codex audit round — that's the next
gate for the planning tree. Files:

- `reporting/plans/strategic_plan_v1.md` — 12-24 month vision, H1-H5
  hypotheses, settled decisions D1-D12, scope-expansion exploration.
- `reporting/plans/tactical_plan_v0_1_x.md` — concrete next 6-8
  releases.
- `reporting/plans/eval_strategy/v1.md` — five eval classes,
  ground-truth methodology.
- `reporting/plans/success_framework_v1.md` — north-star + Tier 1-3
  metrics + anti-metrics.
- `reporting/plans/risks_and_open_questions.md` — 19 risks + 10 open
  questions for maintainer judgement.
- `reporting/plans/README.md` — reading-order index.

The `reporting/plans/historical/multi_release_roadmap.md` is
**SUPERSEDED** by the strategic + tactical pair.

## What's next — your call when you return

Three sensible directions, listed in `post_v0_1_10/`:

1. **Demo work** (Dom's stated next focus) →
   [demo_plan.md](demo_plan.md). The demo plan is scaffolded with
   explicit decision points — Dom needs to confirm scope (audience,
   format, length, what the demo proves) before execution.
2. **Phase 4 audit** (the planning tree gets a Codex review) →
   [phase_4_audit_plan.md](phase_4_audit_plan.md). Same four-round
   pattern as v0.1.10. Ready when Dom is.
3. **v0.1.11 cycle opening** → `reporting/plans/v0_1_11/PLAN.md`.
   Pre-PLAN bug hunt (Phase 0) → PLAN.md → Codex audit. The
   audit-chain integrity release.

These are independent — the demo can run while the Phase 4 audit
or v0.1.11 cycle is in flight, depending on Dom's bandwidth.

## Where things live (reading order for cold start)

1. **`AGENTS.md`** — operating contract (D1-D12 settled decisions).
2. **`README.md`** + **`ARCHITECTURE.md`** + **`REPO_MAP.md`** —
   product story + runtime shape + every directory classified.
3. **`reporting/plans/README.md`** — reading-order index for the
   planning tree.
4. **`reporting/plans/strategic_plan_v1.md`** — strategic frame.
5. **`reporting/plans/tactical_plan_v0_1_x.md`** — execution frame.
6. **This folder** — current "what next" snapshot.

## Verifying the install before the demo

Per the release proof reproduction recipe (already live):

```bash
# Already-installed pipx version should report 0.1.10:
hai --version
hai capabilities --json | python3 -c "import json, sys; print(json.load(sys.stdin)['hai_version'])"

# If not on 0.1.10 yet, refresh:
pipx install --force --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" 'health-agent-infra==0.1.10'

# Doctor check
hai doctor
```

## Gotchas for the next session

Saved as memory entries (will auto-load on session start):

- `feedback_release_paste_safety.md` — zsh + bracketed-paste
  mangles multi-line shell commands; use script files for any
  release-day complex sequence.
- `reference_release_toolchain.md` — `uvx --from build python -m
  build`; project venv has no `build` installed.
- `feedback_pypi_publish_cdn_lag.md` — bypass CDN cache on first
  install attempt with `--no-cache-dir --index-url
  https://pypi.org/simple/`.
- All prior memories about Dom's user/builder modes, narration
  voice, never-assume-data, partial-day handling, etc.

## Session-end state (2026-04-28 13:25 local)

- Working tree: clean post-commit (verify with `git status`).
- HEAD: v0.1.10 release commit on `main`, pushed to `origin`.
- PyPI: `health-agent-infra==0.1.10` live (wheel + sdist).
- Local install: `pipx install` succeeded, `hai 0.1.10` smoke-tested.
- No outstanding actions. Safe to /clear and resume cold.
