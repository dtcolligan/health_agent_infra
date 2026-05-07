Open the v0.2.0 cycle for Phase 3 + Phase 5 (ship). Phases 1+2
closed cleanly in the 2026-05-07 session: W-PROV-2 + 3 doc-only
adjuncts + W-EVCARD-DAILY (mig 027) + W-EVCARD-WEEKLY (mig 028).
Both carriers are tested + ready; W52 consumes them. Branch is
20 commits ahead of origin/main; commit head `da746f5`.

**Goal:** finish v0.2.0. Phase 3 (W52 → W-FACT-ATOM → W58D) plus
Phase 5 (D15 IR + RELEASE_PROOF + freshness sweep + manual TTY
ship gate → `git push` → `twine upload`). Phase 3 floor is
13-20d so a single session likely won't ship — end at a coherent
handoff if not. Do not truncate the audit chain to fit a session
boundary.

**Pre-flight: push if not yet pushed.** Surface git status; if 20
commits are still local, ask whether to `git push origin main`
before opening Phase 3 (your call, not autonomous). The harness
blocks direct push.

Read in this order before any new code:

1. `~/.claude/projects/-Users-domcolligan-health-agent-infra/memory/project_v0_2_0_phase2_complete_2026-05-07.md`
   (resume protocol; commit head; what shipped in Phases 1+2;
   what remains).
2. `~/.claude/projects/-Users-domcolligan-health-agent-infra/memory/project_v0_2_0_phase1_complete_2026-05-07.md`
   (Phase 1 inventory for cross-reference).
3. `reporting/plans/v0_2_0/PLAN.md` §2.D (W52), §2.E (W-FACT-ATOM),
   §2.F (W58D), §3 (ship gates), §4 (risks register).
4. `src/health_agent_infra/core/review/weekly_card.py` —
   `load_canonical_latest_for_week` + `load_full_history_for_week`
   are the helpers W52 consumes for the `--include-history` flag
   (PLAN §2.D acceptance #9).
5. `src/health_agent_infra/core/state/projectors/evidence_card.py`
   — `build_evidence_card_payload` is the daily-card builder W52
   reads from (W52 doesn't write daily cards; synth does that
   already, W52 reads them at aggregation time).
6. AGENTS.md "Settled Decisions" + "Do Not Do" + "Patterns the
   cycles have validated".

**First concrete action — surface scope first, then start W52.**

Surface a 3-5 bullet summary of W52 scope as you understand it
after the read-order, including: aggregation-query shape, abstain
branch threshold, supersession-reconciliation handling,
data-quality `stale_pull` vs `retrospective_manual` distinction,
deferred-domain qualitative-only suppression, and the
`--include-history` flag semantics. Surface that summary, then
propose a W52 commit-cadence plan before writing code (mirror the
Phase 1 / Phase 2 cadence-proposal pattern from this cycle's
shipped commits).

W52 is the cycle's largest workstream (6-9d estimated). Atomic
per-step commits are essential for IR review:

1. SQL aggregation queries (`core/review/weekly.py` new) —
   accepted-state + intent_item + target + recommendation_log +
   x_rule_firing + review_outcome + data_quality_daily +
   sync_run_log + runtime_event_log; filter on
   `superseded_by_plan_id IS NULL`.
2. Partial-week abstain branch logic + threshold load via D13
   contract (`thresholds.toml` `policy.review_weekly`).
3. Data-quality rollup — `stale_pull` vs `retrospective_manual`
   via existing `sync_run_log.mode` (no schema change per
   F-PLAN-04 round-1).
4. Prose builder (`core/review/prose_builder.py` new) — consume
   W-EXPLAIN-UX-CARRY obligations from
   `reporting/docs/explain_ux_review_*.md` per acceptance #7;
   author disposition tracker at
   `reporting/plans/v0_2_0/explain_ux_obligations.md`.
5. Render layer (`core/review/render.py` new) — markdown + JSON.
6. CLI subcommand (`cli/handlers/review.py` extend) + parser-tree
   extension in `cli/__init__.py`. Capabilities-manifest snapshot
   regenerates in lockstep.
7. Weekly claim-card emission inside W52 — uses the
   `project_weekly_card` helper from W-EVCARD-WEEKLY (one card
   per quantitative + comparative atomic claim; qualitative
   atoms emit no card).
8. Test coverage per PLAN §3.1 G2 explicit allocation: ≥23 tests
   in test_review_weekly.py + abstain-metadata + deferred-domain
   suppression + canonical-latest-rerun fixture file. Persona
   matrix re-runs at the end.

After W52 lands cleanly:

9. **W-FACT-ATOM** (PLAN §2.E) — atomic-claim parser. ~2-3d.
   `core/eval/atomic_claims.py` new. ≥98% precision against a
   30-fixture parse corpus at `evals/scenarios/atomic_claims/`.
   Atom types: quantitative, comparative, qualitative.
10. **W58D** (PLAN §2.F) — deterministic factuality gate. ~5-8d.
    `core/eval/factuality_gate.py` new + corpus dir
    `evals/scenarios/factuality/` + manifest `index.json`. ≥150
    fixtures (≥85 known-bad / ≥75 known-good across 5
    sub-categories per the PLAN §2.F table — source-quality,
    x-rule-conflict, source-signal-conflict, source-row-drift,
    audit-ref-orphan). Threshold acceptance: `block ≥97%
    known-bad / pass ≥99% known-good` over the corpus. Threshold
    values in `thresholds.toml` `[policy.factuality_gate]` per
    D13. New flag on `hai review weekly`:
    `--bypass-factuality-gate` (developer-only override; logs
    WARN; `agent_safe=False`; not in capabilities-manifest
    `agent_safe: true` set). Acceptance #6 also extends
    `evals/cli.py` so `--scenario-set all` fans out to
    deterministic + factuality scoring — `judge_adversarial`
    stays shape-only summary.

Then **Phase 5 — ship:**

11. D15 IR rounds. **Empirical norm: 2-3 rounds at 5 → 2 → 1-nit
    settling shape** (twice-validated; v0.2.0 will validate
    again). Auto-draft each round's next prompt at round close
    per `feedback_auto_draft_next_round_prompt.md`; don't ask
    permission.
12. Persona matrix **release gate: 13/13, 0 findings, 0 crashes.**
    Run via `uv run python -m verification.dogfood.runner /tmp/v0_2_0_persona_run`.
13. RELEASE_PROOF.md (tier annotation `**Tier: substantive**`
    first line per D15) + REPORT.md + AUDIT.md entry +
    CHANGELOG.md final reformat (Unreleased → 0.2.0) + ROADMAP.md
    + `reporting/docs/current_system_state.md` + tactical-plan
    next-cycle row freshness sweep per AGENTS.md ship-time
    checklist.
14. Doc-freshness assertion test green
    (`verification/tests/test_doc_freshness_assertions.py`).
15. Manual TTY ship gate — maintainer runs final smoke against
    locally-built wheel before `git push` + `uvx twine upload`.
    Per CLAUDE.md harness rule, the maintainer drives the push +
    upload (not autonomous). PyPI verification per
    `feedback_pypi_publish_cdn_lag.md` — bypass CDN cache on
    first install attempt.

**Honesty boundary gates (G15-G17, PLAN §3.3):**

- G15: RELEASE_PROOF must NOT claim foreign-user empirical
  validation unless W-2U-GATE-2 fired with a transcript (it
  hasn't yet; per D16, opportunistic-not-blocking).
- G16: RELEASE_PROOF must NOT claim LLM-judge factuality.
  v0.2.0 ships W58D deterministic-only; W58J shadow is v0.2.2.
- G17: RELEASE_PROOF must NOT claim insight-ledger persistence.
  v0.2.0 ships claim-cards (per-claim provenance), not
  insight-ledger (multi-week insights). Insight ledger is v0.2.1
  W53.

**Cycle abort triggers (PLAN §3.4) — surface immediately if any
fires; do not silently absorb:**

- W-PROV-2 partial-closure (already shipped clean — no abort).
- W58D cannot meet 97/99 thresholds after corpus + threshold
  revision → cycle abort at G3 with two paths (re-author with
  fresh CP + D14 rerun, OR partial-defer to v0.2.1).
- Effort upper bound (37d) exceeded with W52 not at IR → abort
  at G1 with D14 re-author.
- F-PHASE0-08 absorption decision (defer-default to v0.2.1
  unless ≥10% of fixture-week daily plans affected).
- Schema-group count drift (F-PLAN-R2-04) — single-carrier
  fork-defer is **unsound**; abort + D14 re-author is the path.

**Watchpoints carrying forward (from Phase 1 + 2):**

- Per F-PHASE0-12 + F-PLAN-12: evidence-card payloads carry both
  source-row locators (validated per W-PROV-1) AND audit-chain
  PK references (plain refs, NOT SourceRowLocator). Already
  enforced in `weekly_card.py` validator + `evidence_card.py`
  validator. W52 must respect the split when populating cards.
- Per F-PHASE0-02 + F-PLAN-03: abstain-branch metadata is
  quantitative AND validated outside W58D via deterministic-
  substitution path. No claim cards on abstain.
- Per F-PHASE0-07: multi-canonical day handling — surface BOTH
  non-superseded plans with explicit "multiple plans this day"
  disposition. Maintainer's 2026-04-24 5-version chain is the
  fixture source.
- Per F-PLAN-R3-01: deferred-domain suppression scope is
  quantitative AND comparative factual claims — W52 acceptance
  #8 test pins the literal disposition string.

**Established patterns active** (do not re-litigate):

- Rigor over velocity for architecture/audit tradeoffs
  (`feedback_pick_rigor_over_velocity.md`).
- Run commands; don't print them for git/hai mutations
  (`feedback_run_commands_dont_print_them.md`). Pause only for
  PyPI publish + destructive shared-state ops + foreign-user
  contact.
- Auto-draft each D15 IR round's next prompt at round close
  (`feedback_auto_draft_next_round_prompt.md`).
- Honest partial-closure naming if any W-id undershoots
  (named-defer to v0.2.1 with destination cycle in CARRY_OVER.md).
- Provenance discipline: verify file paths + line numbers + exact
  strings before citing them (AGENTS.md "Patterns the cycles have
  validated").

**Session-end protocol:** if the session ends before v0.2.0
ships, write a fresh `project_v0_2_0_phase3_complete_<date>.md`
or `project_v0_2_0_phase3_partial_<date>.md` memory at session
close naming the cycle state, current commit head, partial-
closure status, and resume protocol. Honest partial-closure
naming applies — do not commit incomplete W52/W-FACT-ATOM/W58D
work as if complete.

If v0.2.0 ships in this session: write `project_v0_2_0_shipped_<date>.md`
and update MEMORY.md to mark v0.2.0 closed.
