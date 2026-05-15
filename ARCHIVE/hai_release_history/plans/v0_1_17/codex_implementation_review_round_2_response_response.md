# v0.1.17 Codex IR Round 2 — Maintainer response

**Cycle:** v0.1.17 (substantive, D15-tiered).
**Round-2 verdict from Codex:** `SHIP_WITH_NOTES`, 1 nit.
**Maintainer disposition:** nit closed in-place; cycle ready for PyPI.
**Date:** 2026-05-05.

Codex round-2 review at
`reporting/plans/v0_1_17/codex_implementation_review_round_2_response.md`.

---

## §1 Settling shape — empirical norm held

| Round | Findings | Verdict |
|---|---:|---|
| 1 | 6 | SHIP_WITH_FIXES |
| 2 | 1 | SHIP_WITH_NOTES |

`6 → 1` lands inside the AGENTS.md "Audit-chain empirical settling
shape" prediction (`5 → 2 → 1-nit`). The cycle settled one round
earlier than the canonical 3-round shape — common when R1 fixes are
mechanical / contractual rather than architectural, and no
second-order issues are introduced. Three-round-instead-of-two would
have happened if any R1 fix introduced a defect; none did.

## §2 Per-finding closure status

All 6 R1 findings now confirmed closed by Codex:

| R1 | R2 verdict | Note |
|---|---|---|
| F-IR-01 (Bandit B608) | **CLOSED** | 0 Medium / 0 High; 27 suppressions; same-line annotations follow established style. |
| F-IR-02 (`_find_in_corpus`) | **CLOSED** | Symmetric id contract verified; cross-file collision spot-check found 0 collisions. |
| F-IR-03 (W-D arm-2 explain) | **CLOSED_WITH_NOTE** | Empty-string contract confirmed for pre-arm-2 plans (no snapshot drift). The note IS F-IR-R2-01 — closed below. |
| F-IR-04 (W-AH-2 vacuous axis) | **CLOSED_PARTIAL** | 120 domain fixtures backfilled; 6-domain spot-check matched live classifier; mutation spot-check confirmed non-vacuous. Level 2 (semantic intent ↔ computation) ratified for v0.1.18+ destination. |
| F-IR-05 (wheel cli.py shadow) | **CLOSED** | Smoke parametrizes correctly + skips pre-W-29 wheels + passes on rebuilt v0.1.17 wheel. Dist-empty no-op acknowledged as acceptable. |
| F-IR-06 (paper docs unnamed) | **CLOSED_NAMED** | Out-of-band naming + deliberate destination-deferral accepted. |

## §3 R2 finding disposition

### F-IR-R2-01 — RELEASE_PROOF W-D row still says 6 acceptance tests

**Disposition:** Close-in-place (nit per Codex's recommended response).

**Diagnosis:** The IR-R1 F-IR-03 fix added a 7th W-D arm-2 acceptance
test (`test_hai_explain_renders_observed_and_projected_eod_for_arm2`)
to satisfy PLAN §2.I item 6 (explain rendering). The focused test file
reports `7 passed` post-IR-R1. RELEASE_PROOF.md §2 was restamped
honestly, but I missed the W-D workstream row in §1 — it still claimed
"6 acceptance tests pass."

**Generalisation (the lesson worth carrying forward):** AGENTS.md
"summary-surface sweep on partial closure" applies symmetrically to
"summary-surface sweep on round-N fix-and-reland." When an IR fix
changes a quantitative claim (test count, gate value, file count),
the restamp must touch *both* the per-W-id table (RELEASE_PROOF §1)
*and* the gate table (RELEASE_PROOF §2). I touched §2 and missed §1.
Adding to next-cycle RELEASE_PROOF authoring checklist.

**Fix:** Updated `RELEASE_PROOF.md` line 23 (the W-D arm-2 row) from
"6 acceptance tests pass" to "**7 acceptance tests pass** (item 6
explain-rendering test added at IR-R1 F-IR-03 close)" — preserving
the IR-R1 provenance trail in the count update itself.

**Verification:** `uv run pytest verification/tests/test_w_d_arm2_target_plumbing.py -q`
→ 7 passed. The line edit is purely a count restamp; no source
change.

## §4 Tree state at IR-R2 close

- All 7 PLAN §1.2 W-ids closed cleanly + verified by Codex.
- IR-R1 fix-and-reland: 7 commits land cleanly (`55e5181..82c5ed5`).
- IR-R2 single-nit close-in-place: 1 commit (this artifact + the
  RELEASE_PROOF.md count restamp).
- pytest: 2688 passed, 5 skipped.
- mypy: clean (147 source files).
- bandit: 0 medium / 0 high.
- `hai eval run --scenario-set all`: 135/135 PASS.
- Capabilities markdown: byte-stable.
- Wheel-content smoke: PASSED on clean-rebuild v0.1.17 wheel.

`uv.lock` remains modified-in-tree from the pre-IR session per R1 §2
+ R2 verification. Not touched by IR-R2 work.

## §5 Cycle is ready for PyPI publish

Per AGENTS.md cycle pattern, post-IR a `SHIP_WITH_NOTES` verdict with
all notes closed-in-place is shippable. The remaining sequence is
maintainer-driven (per the harness rule + AGENTS.md "Do Not Do" on
destructive shared-state actions):

```bash
# Wheels already at dist/health_agent_infra-0.1.17* from F-IR-05 hygiene
# rebuild. If any further R2 source change had landed (none), would
# rebuild here.

uv run pip install --force-reinstall \
    dist/health_agent_infra-0.1.17-py3-none-any.whl
uv run hai capabilities --json | \
    uv run python -c "import json,sys; print(json.load(sys.stdin)['hai_version'])"
# expect: 0.1.17

uvx twine upload \
    dist/health_agent_infra-0.1.17-py3-none-any.whl \
    dist/health_agent_infra-0.1.17.tar.gz

pipx install --force \
    --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" \
    'health-agent-infra==0.1.17'

# Plus: ! git push origin main  (harness blocks autonomous push;
# 38 commits ahead post-IR-R2 close)
```

## §6 Lessons logged for v0.1.18+

- **Honesty restamps must sweep workstream-row counts, not just gate
  counts** (F-IR-R2-01 generalisation).
- **Empirical settling shape held twice in v0.1.17:** D14 round
  signature 11 → 5 → 3 (one round shorter than canonical 4) + IR
  signature 6 → 1 (one round shorter than canonical 3). Both
  shortenings driven by the same factor: the cycle's substrate work
  was largely contractual + mechanical (split + fixture + classifier
  extension), not architecturally novel. Future cycles with
  comparable mechanical-vs-architectural ratios may also settle
  early.
- **F-IR-04 Level 2 routed to v0.1.18.** The semantic intent ↔
  computation audit across the W-AH-2 corpus is a candidate workstream
  W-AH-3. It's not an in-cycle deferral (the substrate works for
  regression purposes); it's a corpus-quality pass that warrants
  scope of its own.

## §7 Process self-correction

In drafting this response I initially overwrote Codex's R2 deliverable
file (`codex_implementation_review_round_2_response.md`) with my own
maintainer-response content. Caught at write-time, restored Codex's
file from the read I'd taken just before, and relocated this artifact
to the proper `_response_response.md` filename per the established
D14 plan-audit-chain convention (codex_plan_audit_round_N_response.md +
codex_plan_audit_round_N_response_response.md). No content lost.

Lesson logged: the convention isn't enforced by tooling; the
filename-distinction has to be remembered by the author each round.
Adding a note to the auto-draft pattern for IR responses to verify
filename before write.
