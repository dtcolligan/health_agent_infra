# Codex External Audit — v0.1.17 PLAN.md (pre-cycle plan review)

> **Why this round.** v0.1.17 PLAN.md was authored 2026-05-04 by
> Claude as the synthesis of (a) v0.1.14 RELEASE_PROOF named-deferred
> items (W-29, W-AH-2, W-AI-2, W-AM-2, W-Vb-4), (b) v0.1.15 round-0
> self-audit cuts assigned destination v0.1.17 (F-PV14-02, W-B,
> W-D arm-2; see `v0_1_15/PLAN.md` §1.4 disposition table rows 5,
> 7, 10), (c) v0.1.15 IR named-deferral (W-C-EQP from F-IR-04 +
> F-IR-R2-02), and (d) the **2026-05-04 v0.1.16-cancellation
> restructure** that promoted v0.1.17 to next-active and retired
> the foreign-user precondition. The cycle ships the deferred
> maintainability + eval-substrate work as one coherent cycle.
>
> **Cycle theme.** Internal correctness + maintainer-side cleanup;
> eval substrate expansion against synthetic + dogfood evidence;
> mechanical refactor cli.py 9927 → 1 main + 1 shared + 11 handler-
> group split (W-29 is the long-deferred AGENTS.md "Settled
> Decisions" v0.1.12 CP1 item, redestinated v0.1.13 → v0.1.14 →
> v0.1.15 → v0.1.17 across the cycle chain); new body-comp intake
> surface (W-B, migration 026).
>
> **No CP-shape governance edits this cycle.** Unlike v0.1.12
> (CP1-CP6 reversed AGENTS.md "Do Not Do" entries), v0.1.17
> proposes only the *closure-side* updates that follow naturally
> from W-29 + W-30 shipping per their existing settled decisions
> (closure of cli.py-split entry; W-30 destination unchanged at
> v0.2.3). PLAN §3 enumerates them. **The audit lever is
> sequencing + sizing + acceptance bite + W-AH-2 honesty boundary,
> not governance reversals.**
>
> **D14 is a settled decision** (added at v0.1.11 ship, twice-
> validated at v0.1.11 + v0.1.12 with the `10 → 5 → 3 → 0` halving
> signature; v0.1.14 + v0.1.15 confirmed at the same shape).
> Empirical norm: 2-4 rounds for a substantive PLAN. v0.1.17 is
> structurally lower-density than v0.1.12 / v0.1.14 (most catalogue
> rows have established source contracts in prior release-proofs),
> so realistic round expectation is 2-3.
>
> **What's different from the v0.1.15 audit.**
>
> 1. v0.1.15 was **foreign-user gate** with W-2U-GATE as the ship
>    claim. v0.1.17 has **no foreign-user precondition** by design
>    (post-v0.1.16-cancellation 2026-05-04). PLAN §1.4 + §4 risk 3
>    name the resulting honesty boundary explicitly: W-AH-2 ships
>    "synthetic-coverage expansion," not "foreign-user-validated
>    coverage." **Q4 + Q8 below probe whether that boundary is
>    enforced consistently across PLAN surfaces.**
> 2. v0.1.17 has **one release-blocker workstream** (W-29) plus 9
>    other W-ids. The release-blocker has a single concrete gate
>    (byte-stable manifest pre/post-split). **Q5 below probes
>    whether W-29's acceptance bites hard enough to actually
>    catch a silent-drift regression.**
> 3. v0.1.17 lifts the **longest-deferred item in the project** —
>    W-29 cli.py split has been on the AGENTS.md "Settled Decisions"
>    books since v0.1.12 CP1, ~6 months ago. The v0.1.13 W-29-prep
>    boundary table is now stale (cli.py grew 8891 → 9927 LOC,
>    +1036 LOC). PLAN §2.A names a re-derivation step at Phase 1
>    open. **Q2 + Q5 below probe whether that re-derivation
>    actually fires before commit, and whether sub-split fallback
>    (intake.py at 1080 LOC pre-W-A absorption) is realistic.**
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit
> is on the *plan document itself* — its coherence, sequencing,
> sizing honesty, hidden coupling, acceptance bite.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main, OR cycle/v0.1.17 if branched (check with maintainer
#         if neither)
git log --oneline -5
# expect top: df6a13c (v0.1.16-cancellation + v0.1.17/18/19
#         restructure commit, 2026-05-04). If top is `2811669`
#         (Phase H conversational intake), you are on the stale
#         /Users/domcolligan/Documents/health_agent_infra/ tree —
#         STOP and surface.
ls reporting/plans/v0_1_17/
# expect: README.md, PLAN.md, codex_plan_audit_prompt.md (this file),
#         cycle_open_session_prompt.md
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`. AGENTS.md "Active
repo path" preamble is durable for exactly this case.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Active repo path" preamble (durable per v0.1.15 W-PLAN-12).
   - "Code Vs Skill" invariant.
   - "Governance Invariants" — W57 still applies; W-B body-comp
     intake is *not* autonomous.
   - "Settled Decisions" D1-D15. **Especially:**
     - **D11 + D14** — pre-PLAN bug-hunt + pre-cycle plan-audit
       patterns this audit enacts.
     - **D15** — cycle-weight tiering. v0.1.17 PLAN's first line
       declares **Tier: substantive**; verify the tier choice is
       honest.
     - **W29 / W30 destination chain** — the multi-cycle redestination
       narrative (v0.1.13 → v0.1.14 → v0.1.15 → v0.1.17). PLAN §3
       proposes the closure-side update. **Verify the framing in
       PLAN §3 is honest about which AGENTS.md sentence updates
       at v0.1.17 ship.**
   - "Do Not Do" — the **cli.py-split entry** that PLAN §3
     proposes to retire at ship (W-29 lifts it). Verify §3's
     proposed-replacement wording quotes the current text
     verbatim.
   - **"Patterns the cycles have validated"** — provenance
     discipline, summary-surface sweep, honest partial-closure
     naming, audit-chain empirical shape. Apply these as you
     audit. **W-Vb-4's three-at-a-time partial-closure pattern
     and W-AM-2's per-scenario validation lesson are the two
     workstreams where these patterns most directly apply.**
2. **`reporting/plans/strategic_plan_v1.md`** — vision (no edits
   this cycle). Verify §10 (Wave 3) does not place a v0.2.x
   schema-group claim on `body_comp` or anywhere W-B's migration
   026 would collide. PLAN §4 risk 5 asserts no collision; verify.
3. **`reporting/plans/tactical_plan_v0_1_x.md` §5D** — this
   cycle's tactical row. **§5C is cancelled v0.1.16; §5E is
   v0.1.18; §5F is v0.1.19; §5G is v0.2.0.** v0.1.17 PLAN §1.4
   restates the renumber narrative — verify it matches §5C
   cancellation note + §5E + §5F.
4. **`reporting/plans/v0_1_17/README.md`** — provisional scope
   (10 W-ids). PLAN §1.2 catalogue should match the README
   table rows; verify per-W-id Title + Effort + Source columns
   reconcile.
5. **`reporting/plans/v0_1_15/PLAN.md` §1.4 disposition table
   + §7 deferred-work register** — provenance for v0.1.15
   round-0 cuts assigned to v0.1.17 (rows 1, 5, 7, 10, 12, 13,
   14, 15 → W-29, F-PV14-02, W-B, W-D arm-2, W-AH-2, W-AI-2,
   W-AM-2, W-Vb-4). PLAN §1.4 chain B should reconcile against
   this.
6. **`reporting/plans/v0_1_14/RELEASE_PROOF.md` §carry-overs +
   §5 out-of-scope** — provenance for W-29 + W-AH-2 + W-AI-2 +
   W-AM-2 (absorbed into W-AI) + W-Vb-4 inheritance into v0.1.15
   then to v0.1.17. PLAN §1.4 chain A should reconcile.
7. **`reporting/plans/post_v0_1_14/carry_over_findings.md`
   §F-PV14-02** — `hai sync purge` source. PLAN §2.G must encode
   the F-PV14-02 contract (≤5-row safety cap; runtime_event_log
   audit; refusal test).
8. **`reporting/plans/post_v0_1_14/agent_state_visibility_findings.md`
   §F-AV-02 + §F-AV-04 arm 2** — W-B + W-D arm-2 sources.
   **Note the doc has a SUPERSEDED header note for the v0.1.15-
   shipped portions** (F-AV-01 / F-AV-03 / F-AV-04 arm 1 / F-AV-05);
   only F-AV-02 + F-AV-04 arm 2 remain in scope here.
9. **`reporting/plans/v0_1_15/codex_implementation_review_response.md`
   §F-IR-04** + **`codex_implementation_review_round_2_response.md`
   §F-IR-R2-02** — W-C-EQP named-defer chain. PLAN §2.J should
   encode the EXPLAIN QUERY PLAN stability assertion against the
   W-A active-window query.
10. **`reporting/docs/archive/cycle_artifacts/cli_boundary_table.md`**
    — v0.1.13 W-29-prep boundary audit (the proposed split table).
    PLAN §2.A inherits it as the starting proposal. **Boundary table
    LOC numbers reflect cli.py at 8891 LOC; current cli.py is 9927
    LOC.** PLAN §2.A acknowledges the staleness and names a re-
    derivation step. Verify §2.A's pre-flight is realistic.
11. **`reporting/plans/v0_1_18/README.md`** + **`v0_1_19/README.md`**
    — downstream cycles. **Confirm v0.1.17 PLAN does NOT pull their
    work forward.** v0.1.18 owns onboarding (W-OB-1..W-OB-6); v0.1.19
    owns the foreign-user empirical contract (renumbered from
    cancelled v0.1.16). PLAN §7 explicitly enumerates these as
    out-of-scope; verify the boundary holds across §2 per-WS sections.
12. **`reporting/plans/v0_1_16/README.md`** — cancellation note
    (read for context on the precondition retirement chain).
13. **`reporting/plans/v0_1_17/PLAN.md`** — the artifact under
    review.

Cross-check that everything PLAN.md cites actually exists in the
tree at the cited path/line. Broken cross-references count as
findings (provenance discipline per AGENTS.md "Patterns the cycles
have validated").

---

## Step 2 — The audit questions

### Q1 — Cycle thesis coherence

PLAN §1.1's stated theme is **"internal correctness + maintainer-
side cleanup; eval substrate expansion against synthetic + dogfood
evidence; mechanical refactor cli.py 9927 → handler-group split;
new body-comp intake surface."**

- **Q1.1.** Does the 10-W-id catalogue add up to that theme, or has
  scope drifted? Specifically: is W-B (new schema, new CLI surface)
  cleanly inside "maintainer-side cleanup" or is it a feature add
  smuggled into a maintainability cycle?
- **Q1.2.** Are the three phases (mechanical foundation / eval
  substrate / carry-overs + nice-to-haves) coherent groupings? Is
  the placement of W-D arm-2 in Phase 3 (rather than Phase 2 with
  the eval-substrate work) honest? W-D arm-2 is a runtime classifier
  fix, not a substrate item — does it belong in Phase 3 or does it
  warrant its own "runtime correctness" phase?
- **Q1.3.** PLAN §1.1 asserts the cycle is parallelizable with
  v0.2.0. Is that actually true given v0.2.0's claimed dependencies
  (per `tactical_plan_v0_1_x.md` §5G)?

### Q2 — Sequencing honesty + W-29 commit serialisation

PLAN §1.3 sequences Phase 1 (W-29 + W-30) before Phase 2/3 to avoid
merging Phase 2/3 cli.py edits into pre-split cli.py. PLAN §4 risk
2 names the serialisation explicitly.

- **Q2.1.** Does PLAN §1.3's serialisation actually hold? Specifically:
  - W-AI-2 (`hai eval review`) adds a CLI surface — confirmed
    sequenced after W-29.
  - F-PV14-02 (`hai sync purge`) adds a CLI surface — confirmed
    sequenced after W-29.
  - W-B (`hai intake weight`) adds a CLI surface — confirmed
    sequenced after W-29.
  - W-D arm-2 wires `hai explain` rendering — does this touch cli.py
    enough to need post-W-29 sequencing? PLAN §1.3 places it in
    Phase 3 implicitly post-W-29; verify.
  - W-AM-2 + W-AH-2 + W-Vb-4 + W-30 + W-C-EQP do not touch cli.py;
    no sequencing constraint — verify by spot-check.
- **Q2.2.** PLAN §2.A's pre-flight names a "re-derivation step" at
  Phase 1 open before W-29 commits. **Does that step actually fire?**
  Or is it a hand-wave with no concrete trigger? The acceptance items
  1-8 don't name the pre-flight as a gate; should they?
- **Q2.3.** OQ-8 escalates "atomic commit vs 3-commit series" for
  W-29. Is the maintainer-ratification path clear? Does PLAN §2.A
  acceptance hold under either choice?

### Q3 — Effort estimate honesty

PLAN §5 totals **25-32-40 days** (per-WS arithmetic + ~5%
coordination + ~10% Phase 0/D14/IR overhead).

- **Q3.1.** W-29 at 4-5-6 days — credible for a 9927-LOC mechanical
  split that must produce zero manifest drift? Compare to v0.1.13
  W-29-prep (boundary audit only — 1 day) and the historical
  estimate "1-2 sessions" cited in earlier PLANs. Is 4-6 d an
  honest range or under-counted because the implementer is the
  same person who knows the codebase?
- **Q3.2.** W-AH-2 at 4-5-6 days for **97-100 new scenarios** —
  ~17-25 scenarios per day. Compare v0.1.14 W-AH (7 new scenarios
  at maybe 1-2 d). Is the throughput claim realistic, or does the
  cycle silently rely on scenario *templates* + bulk-generation
  shortcuts that the acceptance items don't enforce?
- **Q3.3.** W-Vb-4 at 5-6-7 days for 6 personas — credible against
  v0.1.14's 3-personas-in-9-days throughput? PLAN §2.F notes the
  three-at-a-time partial-closure pattern remains available; does
  the effort estimate assume full 6/6 or honest partial?
- **Q3.4.** Total **25-40 days** versus v0.1.15 **15-24 days** —
  v0.1.17 catalogues 10 W-ids (vs v0.1.15 7 W-ids) but the W-29
  release-blocker is uniquely heavy; v0.1.14 closed 35 d for 18
  catalogued slots. Is the 25-40 range internally consistent?

### Q4 — Hidden coupling + the W-AH-2 honesty boundary

PLAN §1.4's renumber narrative names the foreign-user precondition
retirement and asserts W-AH-2 ships "synthetic-coverage expansion,"
not "foreign-user-validated coverage."

- **Q4.1.** Does that honesty boundary hold consistently across
  *every* PLAN surface that cites W-AH-2? Specifically: §1.1
  theme paragraph, §1.2 catalogue Severity column, §1.3 sequencing,
  §2.C body, §4 risk 3, §6 ship gates, §7 out-of-scope. **Missing
  one is the canonical "summary-surface sweep" failure** per
  AGENTS.md "Patterns the cycles have validated."
- **Q4.2.** PLAN §2.C Acceptance item 2 says "every new scenario
  fixture passes its own `expected_*_token` assertion against the
  live classify+policy stack at HEAD." That's the v0.1.14 W-AM
  honest-count lesson applied. Is the assertion mechanism actually
  ship-able, or does it require infrastructure (per-fixture
  validation harness) that isn't in scope?
- **Q4.3.** W-29 + W-30 + capabilities-manifest shape: §6 ship
  gates say W-29 byte-stability is asserted *before* the intentional
  Phase 2/3 adds (W-AI-2, F-PV14-02, W-B); the snapshot regenerates
  at end of cycle to reflect the adds. **Does the ordering actually
  work?** If W-29 commits first and the snapshot must remain pinned
  to pre-W-29 shape, when does the regeneration happen — at end
  of Phase 1 or end of cycle? PLAN §6 says "regenerated against
  post-W-AI-2 + post-F-PV14-02 + post-W-B intentional adds at end
  of cycle." Is that consistent with `test_cli_parser_capabilities_regression.py`'s
  test contract (which asserts against the snapshot file every
  pytest run)?
- **Q4.4.** W-B body-comp ↔ v0.2.x schema-group plan. PLAN §4
  risk 5 asserts no collision. **Verify by reading
  `strategic_plan_v1.md` §10 (Wave 3 schema additions) and
  AGENTS.md "Settled Decisions" entries CP-PATH-A + CP1 + CP2.**
  Does any v0.2.x cycle reach for a body-comp surface that this
  W-B precludes?
- **Q4.5.** W-D arm-2 projection-function default ↔ existing band
  thresholds. PLAN §2.I OQ-5 escalates target-anchored vs linear
  default. Does either default *interact* with the existing
  `nutrition_status` band thresholds in a way the PLAN doesn't
  document? Specifically: if projection emits `projected_eod_kcal
  == target_kcal`, does the classifier cleanly emit `aligned` or
  is there a band-threshold edge case at exact target?

### Q5 — Acceptance criterion bite

PLAN §2.A through §2.J each list acceptance items. The audit's
core question: **could each item actually fail and surface the
bug it's meant to catch?**

- **Q5.1. W-29 acceptance items 2-4** (byte-stable manifest +
  byte-stable parser-tree + byte-stable markdown): asserted by
  `test_cli_parser_capabilities_regression.py`. Does the test
  *currently* run clean against HEAD? If yes, is the test
  scaffold capable of catching subtle parser-tree changes (e.g.
  argparse `dest` rename without surface-name change)? Spot-
  verify by reading the test file.
- **Q5.2. W-29 acceptance item 5** (no group ≥2500 LOC): a new
  test `test_cli_handler_group_loc_ceiling.py` is named. Is the
  2500 ceiling load-bearing or arbitrary? What happens if a
  handler group lands at 2487 LOC and then a v0.1.18 surface
  add tips it to 2510?
- **Q5.3. W-AH-2 acceptance items 1 + 5** (per-domain count
  floor + persona-matrix replay): does item 1's
  `test_scenario_corpus_coverage.py` actually catch a domain
  silently undershooting? Does item 5 actually catch a
  regression introduced by the corpus expansion?
- **Q5.4. W-Vb-4 acceptance item 5** (three-at-a-time partial-
  closure available; no silent partial). Is the gate enforceable
  or does it rely on Codex IR catching missing personas?
- **Q5.5. W-B acceptance items 1-2** (migration test + intake
  test). Does the migration test cover the "v0.1.15.1-shaped
  DB at migration 025" case explicitly, or just an empty DB?
- **Q5.6. W-D arm-2 acceptance item 1** (10am breakfast-only
  with target=3100 → projected=3100 → aligned). Does the test
  assert against the *projection* output specifically, or just
  the band classification (which could pass coincidentally for
  a non-projection reason)?
- **Q5.7. F-PV14-02 acceptance item 1** (3 fixture rows + 1
  audit row). Does it cover the multi-source-multi-date selector
  case, or just single-source single-date?

### Q6 — Settled-decision integrity (closure-side)

PLAN §3 proposes:

1. AGENTS.md "Settled Decisions" W-29 closure update at v0.1.17
   ship.
2. AGENTS.md "Do Not Do" cli.py-split entry retired at v0.1.17
   ship; capabilities-manifest-freeze clause stays.

- **Q6.1.** Does PLAN §3 quote AGENTS.md current text verbatim?
  Specifically: the current "Do Not Do" entry is "Do not split
  `cli.py` or freeze the capabilities manifest schema before
  their scheduled cycles (v0.1.17 / v0.2.3)." PLAN §3 proposes
  the rewritten entry; verify the proposed text against the
  current verbatim.
- **Q6.2.** AGENTS.md "Settled Decisions" entry for W-29 has
  multi-cycle redestination provenance (v0.1.13 → v0.1.14 →
  v0.1.15 → v0.1.17 + v0.1.16 cancellation chain). Does PLAN
  §3 propose updating that provenance trail correctly at ship,
  or does the closure update silently drop the chain?
- **Q6.3.** No new D-entries proposed this cycle. **Is that
  honest?** Specifically: should the post-v0.1.16-cancellation
  empirical-cycle pattern (cancellations require a renamed claim
  if source material fails) be proposed as a D-entry here, or
  does AGENTS.md "Patterns the cycles have validated" already
  cover it? See `v0_1_16/README.md` "Pattern note."

### Q7 — What the plan doesn't say

Absences worth flagging:

- **Q7.1. W-29 abort path.** What happens if W-29's pre-flight
  re-derivation discovers cli.py can't actually be cleanly split
  (e.g., a hidden cross-handler shared state pattern) at the
  current LOC shape? PLAN §2.A names "halt the cycle, escalate
  to maintainer for re-shape" only for the >2500 LOC sub-split
  failure case. What about the more fundamental "split itself
  is wrong-shaped" case the v0.1.13 boundary table named as
  `do-not-split` verdict?
- **Q7.2. Cycle abort overall.** If Phase 1 W-29 lands but
  Phase 2/3 surfaces multi-WS friction beyond what §4 risk 10
  ("sizing residual") covers, does PLAN have a fallback shape?
  v0.1.15 had explicit (a)/(b)/(c) options for the W-2U-GATE
  candidate-availability case; does v0.1.17 have an analogous
  branch?
- **Q7.3. Conditional WS scope.** v0.1.18 README has W-OB-6 as
  conditional. Does v0.1.17 have any analogous conditional
  W-id? W-AM-2's "if a scenario can't fire, drop + log" is
  partly that shape but it's a per-scenario fallback, not a
  whole-WS conditional.
- **Q7.4. Persona runtime expansion** (§4 risk 7). PLAN names
  the risk but does not gate against a worst-case 30+ minute
  persona-matrix runtime. Should there be a runtime-ceiling
  gate, or is "document the new runtime in REPORT.md" enough?

### Q8 — Provenance / external-source skepticism

Spot-verify claims that lean on external/historical docs:

- **Q8.1.** PLAN §2.A claims `cli.py` is **9927 LOC at HEAD
  `df6a13c`**. Verify: `wc -l src/health_agent_infra/cli.py`.
- **Q8.2.** PLAN §2.A claims **+1036 LOC across v0.1.13/v0.1.14/
  v0.1.15/v0.1.15.1** vs v0.1.13's 8891 LOC starting point.
  Verify the v0.1.13 8891 number against the boundary-table doc.
- **Q8.3.** PLAN §2.C claims current scenario count breakdown:
  recovery=5, running=7, sleep=4, strength=3, nutrition=3,
  stress=3, synthesis=10 = 35. Verify by walking
  `src/health_agent_infra/evals/scenarios/`.
- **Q8.4.** PLAN §2.F claims P7..P12 personas exist at
  `verification/dogfood/personas/p[7-12]_*.py`. Verify by
  listing the directory.
- **Q8.5.** PLAN §2.J cites the W-A active-window query verbatim.
  Verify against `src/health_agent_infra/core/intake/presence.py`
  (or wherever the query actually lives at HEAD).
- **Q8.6.** PLAN §2.H proposes migration 026. Verify migration
  head: `ls src/health_agent_infra/core/state/migrations/`.
- **Q8.7.** PLAN cites W57 invariant at `core/target/store.py:
  160-168` (referenced via v0.1.15 PLAN §2.D). Verify the
  current line range (provenance discipline per AGENTS.md).
- **Q8.8.** PLAN §1.4 chain B claims v0.1.15 round-0 cuts were
  "rows 1, 5, 7, 10, 12, 13, 14, 15" of the 16-slot disposition
  table. Verify by reading `v0_1_15/PLAN.md` §1.4.
- **Q8.9.** PLAN §6 cites `test_cli_parser_capabilities_regression.py`
  as the W-29 byte-stability gate. Verify the test file exists
  + pins the snapshot file at the cited path.

### Q9 — Tier annotation honesty (D15)

PLAN's first line declares **Tier: substantive**. Per AGENTS.md
D15: substantive = "≥1 release-blocker workstream, ≥3 governance
or audit-chain edits, OR ≥10 days estimated."

- **Q9.1.** v0.1.17 has 1 release-blocker (W-29) — meets the
  release-blocker criterion. Effort 25-40 d — meets the days
  criterion. **Is the tier choice honest?** Or is v0.1.17
  actually tier-ambiguous (e.g. "hardening" + a single release-
  blocker)?
- **Q9.2.** PLAN §3 proposes only 2 governance/AGENTS.md edits
  (W-29 closure + cli.py-split entry retirement) — under D15's
  "≥3 governance edits" threshold. **Are there hidden governance
  edits in §2 per-WS sections that should also count?**
  Specifically: W-30's regression test scaffolds the v0.2.3
  schema freeze; does that count as a governance edit?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_17/codex_plan_audit_response.md` matching the
existing convention:

```markdown
# Codex Plan Audit Response — v0.1.17 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 1 / 2 / 3 / 4

## Findings

### F-PLAN-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8 / Q9
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-02. ...

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-29 | PASS / FIX / RESCOPE | ... |
| W-30 | ... | ... |
| W-AH-2 | ... | ... |
| W-AI-2 | ... | ... |
| W-AM-2 | ... | ... |
| W-Vb-4 | ... | ... |
| F-PV14-02 | ... | ... |
| W-B | ... | ... |
| W-D arm-2 | ... | ... |
| W-C-EQP | ... | ... |

## Open questions for maintainer

(Specifically rate OQ-1 through OQ-8 in PLAN §8 — agree with the
provisional default? Suggest alternative? Or is the default
already wrong-shaped?)

## Closure recommendation

(Verdict + named must-fix revisions list + recommended next-round
budget.)
```

Each finding must be triageable. Vague feedback is not a finding;
"PLAN.md §2.A claims `cli.py` at 9927 LOC but `wc -l` returns
9928" is a finding. "PLAN seems verbose" is not.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

---

## Step 5 — Out of scope

- Prior-cycle implementation (v0.1.15.1 already audited and
  shipped; v0.1.16 cancelled — not auditable).
- Code changes against this PLAN (Phase 0 hasn't started; no
  W-id has commits yet).
- v0.1.18 / v0.1.19 / v0.2.0 scope (named in tactical_plan_v0_1_x.md
  but not in this PLAN's commitments). Pulling forward is itself
  a finding.
- The strategic + tactical + eval + success + risks docs beyond
  the closure-side §3 deltas this cycle proposes.
- AGENTS.md "Active repo path" preamble (settled v0.1.15
  W-PLAN-12).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14] Codex plan audit ← you are here, round 1
  Maintainer + Claude response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds for
   substantive PLANs; v0.1.17 expectation 2-3)

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix (12 personas; baseline pre-W-Vb-4)
  Codex external bug-hunt audit (optional per maintainer)
  → audit_findings.md consolidates

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds:
  Phase 1 (W-29 + W-30) → atomic Phase 1 commits
  Phase 2 + Phase 3 (8 W-ids, parallelizable post-W-29)
  Codex implementation review (post-implementation, IR)
  ... until SHIP / SHIP_WITH_NOTES (empirical 5 → 2 → 1-nit
  shape; v0.1.17 expectation 2-3 IR rounds)

RELEASE_PROOF.md + REPORT.md → ship to PyPI as 0.1.17
```

Estimated review duration: 1-2 sessions per D14 round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_17/codex_plan_audit_response.md` (new) —
  your findings.
- `reporting/plans/v0_1_17/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_17/codex_plan_audit_round_N_response.md`
  (subsequent rounds, if revisions warrant another pass).

**No code changes.** No test runs. No state mutations. No
implementation against the PLAN.
