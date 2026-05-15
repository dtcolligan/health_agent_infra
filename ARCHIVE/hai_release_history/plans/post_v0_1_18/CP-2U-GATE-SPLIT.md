# CP-2U-GATE-SPLIT — Split W-2U-GATE into install (closed) + wearable + dogfood (deferred), drop v0.2.0 hard dep

**Cycle:** post-v0.1.18 (after v0.1.18 ship 2026-05-06; v0.1.19 cycle
not yet opened).
**Author:** Claude (delegated by maintainer, 2026-05-06 chat).
**Codex verdict:** pending.
**Application timing:** at maintainer approval — adds D16 to AGENTS.md
"Settled Decisions" + cancels v0.1.19 cycle dir + drops v0.1.19 from
the v0.2.0 hard-dep column in `tactical_plan_v0_1_x.md` §1 + adds a
Wave 1 footnote to `strategic_plan_v1.md` §7 naming the gate split.
**Source:** maintainer chat 2026-05-06 — candidate-supply constraint
("the criteria for what is needed is too difficult for me to find")
combined with empirical evidence from a wearable-less foreign-user
session (maintainer's father, post-v0.1.18 install + onboarding,
verbatim "it worked for him").
**Lineage:** successor to `CP-2U-GATE-FIRST` (post-v0.1.13). That CP
sequenced W-2U-GATE first within a cycle. This CP formalizes that the
gate is actually three empirical claims and only one of them is
gating.

---

## Rationale

W-2U-GATE has slipped four times: v0.1.14 → v0.1.15 → v0.1.16
(cancelled 2026-05-04, named candidate became unavailable) → v0.1.19
(empirical-by-design, awaiting candidate). That slip pattern is
evidence the original gate definition was over-specified — one
monolithic gate with one candidate-supply cost.

Empirical reality from the maintainer's post-v0.1.18 install on a
non-maintainer machine surfaces the structural finding: **W-2U-GATE
conflates three different empirical claims that have different
candidate-supply costs**:

1. **W-2U-INSTALL** — does the install + onboarding +
   abstain-without-wearable path work for someone who isn't the
   maintainer? Validates v0.1.18's W-OB-1..7 onboarding work and the
   "honest silence is the feature" bet (H1).
2. **W-2U-WEARABLE** — does the full pipeline (pull adapter →
   classification → cross-domain synthesis → daily plan with
   non-trivial coverage) produce useful output for a wearable-bearing
   foreign user? Validates the recovery / running / sleep / strength
   classifier surface against a non-maintainer signal stream.
3. **W-2U-DOGFOOD** — does a non-maintainer using the system daily
   for ≥7 consecutive days continue to find it useful? Validates
   retention / habit / multi-day audit-chain reconciliation, which is
   different from first-run correctness. This is the strongest
   foreign-user evidence shape and the natural precondition for the
   v0.7 governed-adaptation surface.

W-2U-INSTALL has been **empirically closed** by the maintainer's
father's post-v0.1.18 session (verbal report, no transcript — see
"Residual" below). W-2U-WEARABLE and W-2U-DOGFOOD remain open and
are the surfaces where candidate supply is hard.

The original CP-2U-GATE-FIRST was authored before v0.1.18 existed.
v0.1.18's onboarding-quality cycle retroactively absorbs much of
what the install half of W-2U-GATE was supposed to test;
re-evaluating the gate in light of v0.1.18 + the father's session is
exactly the "settled decisions reopened via CP" path AGENTS.md
prescribes.

This CP is **not** a retreat from foreign-user evidence as a project
discipline. It re-tiers the evidence:

- Install evidence: closed (one foreign-user session post-v0.1.18,
  verbal-only).
- Wearable evidence: opportunistic-not-blocking from v0.2.0 forward;
  re-evaluated as a hard gate at the v0.4 review when MCP read-
  surface decisions need it.
- Dogfood evidence (≥7d daily use): same v0.4 review re-evaluation.

## Current AGENTS.md text

No D16 exists. "Settled Decisions" ends at D15 (cycle-weight tiering,
v0.1.12 CP3, AGENTS.md:237-257).

## Proposed delta — add to AGENTS.md "Settled Decisions" (after D15)

```
- **(D16, post-v0.1.18) W-2U-GATE split.** Foreign-user empirical
  evidence is three gates, not one. **W-2U-INSTALL** (install +
  onboarding + abstain-without-wearable produces coherent output for
  a non-maintainer) is closed by the post-v0.1.18 foreign-user
  session (maintainer's father, 2026-05-06; verbal-only closure, no
  transcript). **W-2U-WEARABLE** (full pipeline produces useful
  output for a wearable-bearing foreign user) and **W-2U-DOGFOOD**
  (non-maintainer uses the system daily for ≥7 consecutive days) are
  deferred to opportunistic-not-blocking from v0.2.0 forward, both
  re-evaluated as hard gates at the v0.4 review when MCP read-
  surface decisions require foreign-user evidence. v0.2.0 hard-deps
  drop the foreign-user empirical row; v0.2.0's only remaining hard
  dep is v0.1.14 substrate (W-PROV-1 + W-AJ). The named residual:
  v0.2.0 ships its W52 weekly-review surface without a wearable-
  bearing or multi-day foreign-user session having run against it;
  the W58D factuality gate is the structural mitigation. The
  W-2U-INSTALL closure is verbal-only and a future cycle's D14 may
  flag this as weak provenance. Origin: post-v0.1.18
  CP-2U-GATE-SPLIT.
```

## Proposed delta — `reporting/plans/tactical_plan_v0_1_x.md` §1

**Row v0.1.19** (currently line 51): replace cell content with the
cancelled-cycle shape used for v0.1.16 (line 48). Strikethrough the
release name; rewrite the theme cell to point at `v0_1_19/README.md`
+ this CP; date columns become `n/a`.

**Row v0.2.0** (currently line 52), "hard deps" column:

**Before:**
> v0.1.19 (foreign-user session fixes consolidated, formerly v0.1.16)
> + v0.1.14 (W-PROV-1 + W-AJ judge harness). **NOT** dependent on
> v0.1.17 — runs in parallel.

**After:**
> v0.1.14 (W-PROV-1 + W-AJ judge harness). **NOT** dependent on
> v0.1.17 — runs in parallel. **Foreign-user empirical evidence
> re-tiered to opportunistic-not-blocking per CP-2U-GATE-SPLIT
> (post-v0.1.18, AGENTS.md D16):** v0.1.19 cancelled; W-2U-INSTALL
> closed (verbal-only) by the post-v0.1.18 father session;
> W-2U-WEARABLE + W-2U-DOGFOOD deferred to v0.4 review.

**Prose immediately after the table** (currently lines 57-72) needs
the v0.1.19 reference removed from the forward-sequence narrative
and replaced with a one-line reference to D16 / this CP.

## Proposed delta — `reporting/plans/v0_1_19/README.md`

Replace the existing "Status: scoped as empirical-by-design" prose
with a cancellation note matching `reporting/plans/v0_1_16/README.md`
shape. The new content is set out under "Affected files" → file
contents below.

## Proposed delta — `reporting/plans/strategic_plan_v1.md` §7 Wave 1

Append a footnote / annotation to the Wave 1 paragraph
("Hardening + dogfood credibility (v0.1.10–v0.1.13, ~3 months)",
currently lines 446-454):

```
**Footnote (post-v0.1.18 CP-2U-GATE-SPLIT, AGENTS.md D16).** Wave 1's
"external reviewer reading the project cold can verify the
governance contract holds" end-state held empirically through
v0.1.18, but the foreign-user empirical contract bifurcated into
install-validation (closed at v0.1.18, verbal-only), wearable-
validation (deferred to v0.4 review), and dogfood-validation
(≥7d daily non-maintainer use, deferred to v0.4 review). The Wave 1
end-state is therefore *partly* validated; full foreign-user
wearable-bearing + multi-day dogfood evidence moves to Wave 3
prereq territory.
```

§9 ("What v1.0 looks like") needs no change — the v1.0 ship gate
already requires "persona matrix passes all 8 archetypes" + external-
reviewer audit-chain reconciliation, which are independent of
W-2U-WEARABLE and W-2U-DOGFOOD.

## Proposed delta — v0.2.0 PLAN.md (when authored)

Add a §-residual-risks entry:

```
**Foreign-user wearable-bearing + multi-day evidence is missing.**
W-2U-WEARABLE and W-2U-DOGFOOD deferred per CP-2U-GATE-SPLIT
(D16). v0.2.0's W52 weekly-review surface ships without having
survived a foreign-user wearable-bearing or ≥7-day session.
Mitigations: (1) W58D deterministic factuality gate rejects any W52
prose claim not grounded in source rows; (2) the persona matrix
continues to exercise the synthesis surface across 8+ archetypes;
(3) a v0.2.0 post-publish foreign-user session may surface findings
that carry forward to v0.2.1. The W-2U-INSTALL closure is verbal-
only (no transcript) and may be re-flagged by v0.2.0 D14.
Re-evaluation gate: v0.4 review.
```

## Residual claim — W-2U-INSTALL closure quality (verbal-only)

The closure claim depends on the maintainer's father's session being
treated as W-2U-INSTALL evidence. The evidence is verbal-only ("it
worked for him") with no transcript at
`reporting/plans/v0_1_19/foreign_machine_session_<YYYY-MM-DD>.md` and
none planned (maintainer chat 2026-05-06: "I cannot get father
transcript").

**This residual is named, not hidden.** Three audit-chain
implications:

1. Future cycles' D14 may flag the closure as weak provenance. That
   is correct behaviour — the residual is real. The CP names it
   explicitly to short-circuit the round-2 finding ("D16 cited a
   verbal-only closure").
2. v0.2.0 PLAN's §-residual-risks block (above) carries the
   weakness forward. v0.2.0 RELEASE_PROOF should not claim
   foreign-user empirical validation.
3. If a wearable-bearing or ≥7d-dogfood foreign-user session runs at
   any point pre-v0.4, treat its transcript as **closure evidence
   for both W-2U-WEARABLE/W-2U-DOGFOOD and a retro-strengthening of
   W-2U-INSTALL** (the transcript will incidentally cover the
   install path).

## Affected files

- `AGENTS.md` — add D16 entry to "Settled Decisions" (after D15,
  before "## Release Cycle Expectation").
- `reporting/plans/tactical_plan_v0_1_x.md` — v0.1.19 row marked
  cancelled (matching v0.1.16 strikethrough shape); v0.2.0 row hard-
  deps column updated; §2 prose cross-reference updated.
- `reporting/plans/v0_1_19/README.md` — replace with cancellation
  note (content drafted alongside this CP).
- `reporting/plans/strategic_plan_v1.md` — §7 Wave 1 footnote.
- `reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md` — this file
  (new directory; matches `post_v0_1_15/` precedent for inter-cycle
  artifacts).

**No transcript file** — closure is verbal-only per maintainer
2026-05-06.

## Dependent cycles

- **v0.2.0** — direct beneficiary; hard-dep drops; opens without
  v0.1.19 closure.
- **v0.2.0–v0.2.3** — opportunistic foreign-user-session absorption
  via PLAN carry-forward workstreams (any session that materializes
  during v0.2.x carries forward without re-tiering the gate).
- **v0.4 review** — re-evaluation gate for both W-2U-WEARABLE and
  W-2U-DOGFOOD; if MCP read-surface design (Wave 3) requires
  wearable-bearing or multi-day foreign-user evidence as a security
  / UX gate, both re-tier to hard at that point.
- **v0.1.17, v0.1.18** — no impact; both shipped.

## Acceptance gate

- `accepted`: AGENTS.md gains D16; tactical plan §1 row v0.2.0
  hard-deps drops v0.1.19; tactical plan v0.1.19 row marked
  cancelled; v0.1.19 README replaced with cancellation note;
  strategic plan §7 Wave 1 footnote added; post_v0_1_18 directory
  created with this CP archived. **No transcript file.**
- `accepted-with-revisions`: gate split intact (the load-bearing
  claim); destination cycles, gate naming, or duration thresholds
  may revise. The four non-negotiable elements: (a) the split into
  three gates, (b) v0.2.0 drops the v0.1.19 hard dep, (c)
  W-2U-WEARABLE + W-2U-DOGFOOD deferred to v0.4 review, (d) the
  W-2U-INSTALL closure is named as verbal-only.
- `rejected`: AGENTS.md unchanged; v0.1.19 stays open as
  empirical-by-design; v0.2.0 hard-dep on v0.1.19 stays; maintainer
  continues candidate search. **Implication of rejection:** v0.2.0
  is indefinitely blocked on candidate supply.

## What would change my mind on the recommendation

Three signals that would pull this CP back:

1. A wearable-bearing foreign-user candidate materializes within ~2
   weeks of CP authoring — recommendation flips to "park CP, run
   v0.1.19 as planned."
2. The maintainer reverses the no-transcript decision and captures
   a father transcript — recommendation amends the W-2U-INSTALL
   closure from verbal-only to transcript-grounded.
3. Maintainer's downstream plan (v0.2.0 PLAN draft) reveals a
   workstream that genuinely cannot ship without wearable-bearing
   or ≥7d foreign-user evidence — recommendation flips to "hold
   the gate; redefine candidate criteria more aggressively."

Absent those signals, the recommendation stands.
