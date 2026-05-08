# Maintainer Response — v0.1.13 D14 Round 2

**Date:** 2026-04-30.
**Author:** Claude (delegated by maintainer Dom Colligan).
**Round under response:** 2
**Codex round-2 verdict:** PLAN_COHERENT_WITH_REVISIONS (7 findings).
**This response disposition summary:** all 7 findings accepted; 0
disputed; 0 deferred. All 7 are second-order regressions
introduced by my round-1 revisions — exactly the pattern I
explicitly anti-checked for in the round-1 maintainer response and
that AGENTS.md "Patterns the cycles have validated" warns about.
The anti-check list at the bottom of round-1 response named 5
risks; round 2 found 5 of them (R2-01 + R2-02 + R2-03 + R2-04 +
R2-05) plus 2 I missed entirely (R2-06 + R2-07).

The empirical 10 → 5 → 3 → 0 settling shape predicts ~3 round-3
findings on a substantive 17-WS PLAN. With the second-order
regressions now drained, round 3 should mostly catch tertiary
issues or genuine new gaps round 1+2 didn't surface.

---

## Finding-by-finding disposition

### F-PLAN-R2-01 — Opening summary stale

**Disposition:** ACCEPT.

The header "Status" block was the most visible round-1 omission.
Updated:

- "D14 plan-audit chain not yet opened" → "in progress" with
  round-1 + round-2 outcomes recorded.
- "16 workstreams" → "17 workstreams (per F-PLAN-01)" in tier
  rationale.
- "First commit cherry-picked" → "Two commits cherry-picked" with
  both SHAs (`636f5d3` code+test diff, `a10a238` RELEASE_PROOF
  doc) named explicitly.

This is the canonical "summary surface drift" v0.1.12 IR caught at
round 2; I should have updated the header at round-1 response
time but missed it because the header isn't on the audit-prompt
reading-order list.

**Edit sites:** PLAN.md "Status" block + "Branch" block
(lines 3-12 + 41-43 in the round-1 file, now lines 3-13 + 41-46).

### F-PLAN-R2-02 — W-Vb-3 fork-defer scope incomplete + placeholder slugs

**Disposition:** ACCEPT WITH SCOPE EXPANSION.

I had assumed the persona matrix was 6 personas (P1+P4+P5 in,
P9+P11+P12 out). Codex correctly identified the matrix has 12
personas. The 9 non-ship-set personas
(P2/P3/P6/P7/P8/P9/P10/P11/P12) all defer to v0.1.14 W-Vb-3.

Concrete slugs (read from `verification/dogfood/personas/__init__.py`
lines 20-31):

- P4 = `p4_strength_only_cutter`
- P5 = `p5_female_multisport`
- P1 = `p1_dom_baseline` (already concrete)

Placeholder `<slug>` notation replaced with concrete slugs in §2.A
contract acceptance + §3 ship-gate row. §1.3 + §4 + CARRY_OVER §4
all updated to enumerate the 9-persona residual.

**Edit sites:** §1.2.A W-Vb catalogue row, §1.3 W-Vb-3 row, §2.A
W-Vb files list + acceptance section (full rewrite of acceptance
to use concrete slugs), §3 ship-gates demo-regression row, §4
risks register W-Vb row, CARRY_OVER §4 W-Vb-3 row (expanded scope
+ revision-2 timestamp).

### F-PLAN-R2-03 — W-CARRY acceptance check claims §2 owns everything

**Disposition:** ACCEPT.

The source table in `v0_1_12/CARRY_OVER.md` §3 mixes v0.1.13 in-
cycle items with v0.1.14+ pass-through defers. v0.1.13 CARRY_OVER
§2 owns the in-cycle rows; §4 owns the pass-through rows. The
acceptance check at the bottom incorrectly claimed §2 covered
everything.

Acceptance check revised to require disposition in §2 (in-cycle)
**or** §4 (later-cycle pass-through), with explicit note that the
source table is split across both by destination cycle.

**Edit sites:** CARRY_OVER.md acceptance-check bullet for
reconciliation §6 v0.1.13+ items.

### F-PLAN-R2-04 — W-AD `cli.py` paths still unprefixed

**Disposition:** ACCEPT.

My round-1 grep for unprefixed paths used pattern
`^\`cli\.py` (line-anchored) which doesn't match inline references
in table cells. Both the §1.2.B catalogue row and the §2.B contract
prose for W-AD still cited bare `cli.py`. Both updated to
`src/health_agent_infra/cli.py`.

This is exactly the path-prefix completeness risk I named in the
round-1 anti-check list ("Quick grep for `core/`, `domains/`,
`cli.py` without `src/health_agent_infra/` prefix would catch any
I missed") — the grep was correct in spirit but anchored too
strictly. Lesson for future revision rounds: use unanchored grep
for inline references.

**Edit sites:** §1.2.B W-AD catalogue row, §2.B W-AD contract.

### F-PLAN-R2-05 — W-AE "four cause classes" lists five outcomes

**Disposition:** ACCEPT.

Both PLAN.md §2.B W-AE acceptance and the new triage doc
`reporting/docs/intervals_icu_403_triage.md` had the same off-by-
one bug — claiming "four cause classes" while listing five
outcomes (`OK` + `CAUSE_1_CLOUDFLARE_UA` + `CAUSE_2_CREDS` +
`NETWORK` + `OTHER`).

Reframed as **"five outcome classes (one success + four failure
classes)"** in both surfaces. The triage doc's "How `hai doctor
--deep` consumes this" section now structures the list as
"Success (1)" / "Failure classes (4)" so the count is unambiguous.

**Edit sites:** §2.B W-AE acceptance + triage doc §"How `hai
doctor --deep` consumes this".

### F-PLAN-R2-06 — W-LINT allowlist names non-existent `research` skill

**Disposition:** ACCEPT WITH CORRECTION.

I had paired `research` with `expert-explainer` in the allowlist
without verifying the packaged skills directory. There is no
packaged `research` skill — the only research surface in the
project is the code-owned `core/research/` registry + `hai
research` CLI command, both of which are CLI/runtime surfaces
that already run the strict regime per constraint (4).

Allowlist corrected to `expert-explainer` only (the single
packaged skill whose explicit purpose is bounded definitional /
quoted explanation). Allowlist constraint reframed as "packaged-
skill allowlist" to make it explicit that code surfaces never
qualify. Expandable per future packaged skills that need it.

I verified the actual skills directory:
`src/health_agent_infra/skills/` contains 14 packaged skills,
none named `research`. The corrected allowlist is honest about
v0.1.13 ship-set being one skill.

**Edit sites:** §2.C W-LINT constraint (1) — full rewrite of the
allowlist clause.

### F-PLAN-R2-07 — Risk-cut effort math wrong

**Disposition:** ACCEPT.

Math error: 22.5-32.5d minus 3-4d (W-AC at 1-2d + W-AF at 1d +
W-AK at 1d) = 19.5-28.5d, not 18.5-25.5d.

I likely carried forward the original v0.1.13 PLAN's "18-25 days"
cut-target (which was 4-7d off the original 22-32d baseline)
without rebasing when I revised the baseline to 22.5-32.5d. The
named cuts only produce 3-4d of savings; the cut-target arithmetic
must update with the baseline.

§5 corrected to **19.5-28.5 days** with explicit math shown
inline ("3-4d savings from named cuts").

**Edit sites:** §5 effort-estimate cut-target line.

---

## Answers to Codex's open questions

1. **W-Vb long-term universe?** All 12 personas eventually. The
   matrix at `verification/dogfood/personas/__init__.py` defines
   12; v0.1.13 W-Vb closes 3 (P1+P4+P5); v0.1.14 W-Vb-3 covers
   the 9-persona residual (P2/P3/P6/P7/P8/P9/P10/P11/P12) and
   may further partial-close at v0.1.14 cycle scoping. The end
   state is every matrix persona has a packaged demo fixture.

2. **W-LINT allowlist scope?** Packaged skill names only. Code-
   owned research surfaces (e.g., `core/research/` registry, `hai
   research` CLI) are not allowlisted because constraint (4) of
   the W-LINT exception path explicitly says CLI rendering paths
   never get the exception, regardless of provenance. v0.1.13
   ship-set is `expert-explainer` only; expandable per future
   packaged skills with bounded definitional / quoted explanation
   purpose.

---

## What round 3 should re-verify (anti-self-introduced-regression)

Round 1 → round 2 produced 5 of the 5 anti-checks I named, plus
2 I missed. For round 3, the active anti-check list:

- **F-PLAN-R2-01 propagation completeness.** Header status block
  now says "round-1 closed, round 2 closed." Round 3 should verify
  no other narrative surface in the PLAN still says "this is the
  round-1 input" or "16 workstreams." Quick grep:
  `grep -n "round-1 input\|16 workstreams" PLAN.md` should return
  no hits.
- **F-PLAN-R2-02 W-Vb-3 scope coherence.** The 9-persona enumeration
  now appears in PLAN §1.3 + §2.A acceptance + §3 ship-gate row +
  §4 risks register + CARRY_OVER §4. Round 3 should verify all
  five surfaces enumerate the same 9 personas (P2/P3/P6/P7/P8/
  P9/P10/P11/P12) and not a different subset.
- **F-PLAN-R2-04 path-prefix completeness, second pass.** I should
  have caught W-AD with my round-1 grep but missed it due to
  pattern anchoring. Round 3 grep:
  `grep -n " \`core/\| \`domains/\| \`cli\.py\| \`evals/" PLAN.md`
  (unanchored) should return no hits.
- **F-PLAN-R2-05 cause-class count consistency.** Both PLAN and
  triage doc now use "five outcome classes." Round 3 should verify
  no other surface (e.g., the §3 ship-gate row "intervals.icu
  triage doc") still implies a different count.
- **F-PLAN-R2-06 allowlist content vs constraint wording.** The
  W-LINT exception now allowlists only `expert-explainer`. Round 3
  should verify (a) the §3 ship-gate row "Regulated-claim lint"
  doesn't reference the old `research`/`expert-explainer` pair;
  (b) the constraint (4) "ordinary user-facing prose still
  blocked" wording covers code surfaces consistently.
- **F-PLAN-R2-07 effort math propagation.** §5 now says 19.5-28.5d
  cut-target. Round 3 should verify (a) §1.2 baseline still says
  22.5-32.5d; (b) §4 risks register row "17-workstream scope" math
  still works; (c) the round-1 maintainer response's "5 calendar
  weeks" claim still reconciles with 22.5-32.5d at 4h/day.
- **CARRY_OVER §4 timestamp / revision marker.** I added "expanded
  2026-04-30 r2" to the W-Vb-3 row. Round 3 should verify other
  rows that revised this round (acceptance check) carry similar
  markers or that the acceptance-check revision is timestamped
  honestly.
- **F-PLAN-R2 finding citation propagation.** The maintainer
  response cites F-PLAN-R2-NN; revisions in PLAN.md likewise.
  Round 3 should verify no F-PLAN-R2-N citation in the PLAN points
  to a finding that isn't in `codex_plan_audit_response_round_2_response.md`.

If round 3 returns ≤ 3 findings (per the empirical norm), the
audit chain is ready to close at round 4 with PLAN_COHERENT.

---

## Provenance — files modified in response to round 2

| File | Change shape | Codex finding(s) |
|---|---|---|
| `reporting/plans/v0_1_13/PLAN.md` | Header status block + W-Vb section + W-AD paths + W-AE wording + W-LINT allowlist + §5 math | F-PLAN-R2-01, 02, 04, 05, 06, 07 |
| `reporting/plans/v0_1_13/CARRY_OVER.md` | §4 W-Vb-3 expanded scope + acceptance check revised | F-PLAN-R2-02, 03 |
| `reporting/docs/intervals_icu_403_triage.md` | "How hai doctor --deep consumes this" section restructured | F-PLAN-R2-05 |
| `reporting/plans/v0_1_13/codex_plan_audit_round_2_response_response.md` | This file | (response convention) |

All edits committed as a single commit on cycle/v0.1.13 alongside
this response. Branch state ready for D14 round 3.
