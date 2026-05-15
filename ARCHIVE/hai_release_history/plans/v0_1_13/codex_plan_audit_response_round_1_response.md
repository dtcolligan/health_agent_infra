# Maintainer Response — v0.1.13 D14 Round 1

**Date:** 2026-04-30.
**Author:** Claude (delegated by maintainer Dom Colligan).
**Round under response:** 1
**Codex round-1 verdict:** PLAN_COHERENT_WITH_REVISIONS (11 findings).
**This response disposition summary:** all 11 findings accepted; 0
disputed; 0 deferred. Revisions applied to PLAN.md + CARRY_OVER.md
+ one new in-repo doc + one cherry-pick. Ready for D14 round 2.

The empirical 10 → 5 → 3 → 0 settling shape predicts ~5 round-2
findings on a substantive 17-WS PLAN. Most likely shape: second-
order regressions from THIS round's edits (the "summary surface
sweep" trap that v0.1.12 IR round 2 caught) + late-surfacing
provenance errors in the parts of the PLAN that round 1 didn't
read deeply.

---

## Finding-by-finding disposition

### F-PLAN-01 — Catalogue count off by one

**Disposition:** ACCEPT.

W-CARRY has its own per-WS contract in §2.C, so it IS a workstream,
not cycle scaffolding. Headline updated 16 → 17. Effort range
22-32d → 22.5-32.5d. Risk-register row updated 16 → 17.

**Edit sites (provenance for round-2 verification):** PLAN.md
"Total scope" line + "Approximate effort" line + §4 risks register
row "16-workstream scope exceeds single-contributor 4-week budget"
(now: "17-workstream scope ... 5-week budget").

### F-PLAN-02 — CARRY_OVER §2 missing two source rows

**Disposition:** ACCEPT.

Added two new rows to CARRY_OVER §2 with explicit cross-references
to §1: one for L3 §6.3 strategic-plan framing edit (CP6
application), one for W-FBC-2. Both rows tagged "(also covered by
§1)" and explain the duplication is for honest acceptance-check
coverage. The acceptance check #2 wording at the bottom of
CARRY_OVER stays unchanged because the rows now make the claim
true.

**Edit sites:** CARRY_OVER.md §2, two new rows below the original
four.

### F-PLAN-03 — Hotfix RELEASE_PROOF path broken in cycle tree

**Disposition:** ACCEPT.

Cherry-picked commit `b570766` from `hotfix/v0.1.12.1` into
`cycle/v0.1.13`. The hotfix RELEASE_PROOF
(`reporting/plans/v0_1_12_1/RELEASE_PROOF.md`) now exists in-tree
on the cycle branch as commit `a10a238`. The cycle branch
inheritance is now: code+test diff (commit 636f5d3) +
RELEASE_PROOF doc (commit a10a238) from the hotfix branch; version
bump + CHANGELOG entry NOT cherry-picked (those are hotfix-branch-
only because cycle/v0.1.13 will eventually bump to 0.1.13).

CARRY_OVER §5 prose updated to reflect both cherry-picks honestly.

**Edit sites:** new commit on cycle/v0.1.13 (a10a238) + CARRY_OVER.md
§5 prose under the W-CF-UA row.

### F-PLAN-04 — Runtime paths missing `src/health_agent_infra/` prefix; W-N-broader file list provenance gap

**Disposition:** ACCEPT.

Two distinct edits:

1. Added `src/health_agent_infra/` prefix to every runtime path in
   PLAN.md. Affected sections: §1.2.A W-Vb + W-N-broader + W-FBC-2
   catalogue rows, §2.A W-Vb + W-N-broader + W-FBC-2 contract
   sections, §2.B W-AA + W-AE files lists, §2.C W-LINT files list.
2. W-N-broader file list reframed from "per v0.1.12
   audit_findings.md" (false provenance) to "initial search surface
   to validate during Phase 0 against the actual `-W error::Warning`
   failure list." Also propagated to §4 risks register
   ("authoritative file list derived from a fresh `pytest -W
   error::Warning` run at Phase 0 open").

The second edit honestly acknowledges that I composed the list
from heuristic guesses + v0.1.12 audit_findings.md notes, not from
a verified per-site failure dump. Phase 0 D11 will produce the
authoritative list.

**Edit sites:** ~7 places in PLAN.md across §1.2 + §2 + §4.

### F-PLAN-05 — W-Vb fixture path conflicts with shipped loader

**Disposition:** ACCEPT.

Reverted the proposed per-persona-directory shape. PLAN.md now
correctly references the existing single-JSON-per-persona shape
(`p1_dom_baseline.json`, `p4_<slug>.json`, `p5_<slug>.json`) and
explicitly notes the loader contract at
`src/health_agent_infra/core/demo/fixtures.py` is preserved (no
loader / package-data migration). My original PLAN was wrong; the
existing shape is fine and ships unchanged.

**Edit sites:** §1.2.A W-Vb catalogue row + §2.A W-Vb files list.

### F-PLAN-06 — W-Vb partial-closure drift (catalogue full / contract partial / ship-gate P1-only)

**Disposition:** ACCEPT WITH HONEST PARTIAL-CLOSURE NAMING.

Per AGENTS.md "Honest partial-closure naming" pattern:

- Ship-set is **P1 + P4 + P5** (three personas) — covers
  `dom_baseline` plus two contrast personas. Each gets full
  DomainProposal seeds across all 6 domains.
- P9 + P11 + P12 (the three remaining of the 12-persona matrix) are
  **fork-deferred to v0.1.14 W-Vb-3** with destination cycle
  named in PLAN §1.3 + CARRY_OVER §4.
- Acceptance criteria in §2.A revised to assert each of the three
  ship-set personas reaches `synthesized` (not just P1).
- Ship-gate row in §3 revised to require all three named personas.

This is the same pattern v0.1.12 applied to W-Vb (partial closure
→ v0.1.13 W-Vb) and W-FBC (partial closure → v0.1.13 W-FBC-2).
v0.1.13 inherits two of those and adds a third (W-Vb-3) for
v0.1.14.

**Edit sites:** §1.2.A W-Vb row, §1.3 out-of-scope table (new W-Vb-3
row), §2.A W-Vb contract acceptance, §3 ship gates demo-regression
row, §4 risks W-Vb row, CARRY_OVER §4 (new W-Vb-3 row).

### F-PLAN-07 — W-FBC-2 reopens out-of-scope option C

**Disposition:** ACCEPT.

PLAN.md was wrong to imply option C is on the table.
`reporting/docs/supersede_domain_coverage.md` lines 49-50 explicitly
say option C "Not in scope for v0.1.x." v0.1.13 doesn't reopen that;
the PLAN's wording was sloppy.

W-FBC-2 contract revised to:

- Option A is the documented default (no per-domain fingerprint
  needed).
- Option B is the only design fork available; ship the per-domain
  fingerprint primitive ONLY if option B is selected at design.
- Option C is explicitly out-of-v0.1.x scope per the existing
  design doc; not reopened by v0.1.13.

§4 risks register entry revised to "option A default vs option B
fork" instead of "option A vs B vs C deferred."

**Edit sites:** §2.A W-FBC-2 sub-deliverable #3, §4 risks W-FBC-2
row.

### F-PLAN-08 — W-AA wall-clock SLO not measurable

**Disposition:** ACCEPT.

Split into two distinct gates per Codex's recommended response:

1. **Deterministic test gate (the actual ship-gate):**
   `test_init_onboarding_flow.py` runs with stubbed input + stubbed
   intervals.icu (replay-client shape, same as existing
   `ReplayWellnessClient`). Asserts `synthesized` in a single test
   invocation. Independent of network, hardware, keyring prompts.
2. **Operator demo SLO (target, not ship-gate):** documented in a
   new `reporting/docs/onboarding_slo.md` with caveats (broadband,
   modern hardware, credentials at hand). "Still pulling" is
   explicitly an allowed degraded state, not an SLO failure. NOT
   a CI gate; manual demo protocol only.

The ship-gate row in §3 split into two rows accordingly. The §4
risks register row reframed to call out the SLO conflict resolution
explicitly.

**Edit sites:** §2.B W-AA acceptance section (full rewrite), §3 ship
gates (two rows replace one), §4 risks register entry.

The new `reporting/docs/onboarding_slo.md` will be authored as
part of W-AA implementation, not at PLAN time. Calling that out
here so a future round doesn't catch it as a "doc cited but not
present."

### F-PLAN-09 — W-LINT exception path lacks non-loophole gate

**Disposition:** ACCEPT WITH 4-CONSTRAINT GATE.

Exception path now requires ALL FOUR of:

1. **Allowlisted surface only.** Hard-coded skill allowlist
   (initially: `research`, `expert-explainer`). CLI rendering paths
   never get the exception.
2. **Citation required.** Each occurrence accompanied by a
   provenance citation against the allowlisted research source
   registry under `src/health_agent_infra/core/research/`.
3. **Quoted-term context only.** Term must appear in quote /
   attribution / definitional context, not first-person claim.
4. **Ordinary user-facing prose still blocked.** Non-allowlisted
   skill rationale + all CLI rendering paths run strict regime.

Acceptance adds a `test_regulated_claim_exception_bounded` negative
test asserting each individual constraint causes the lint to fail
when violated. This prevents the exception from becoming a
wholesale loophole.

§4 risks register row reframed accordingly.

**Edit sites:** §2.C W-LINT contract (constraints + acceptance —
substantial expansion), §3 ship gates row (now requires both lint
test + bounded-exception negative test), §4 risks register row.

### F-PLAN-10 — W-AE depends on triage script not in repo

**Disposition:** ACCEPT.

Authored `reporting/docs/intervals_icu_403_triage.md` (in-tree,
versioned project artifact) from the content of the private memory
note. The doc:

- Documents the two distinct 403 root causes (Cloudflare UA-block
  vs genuine credential rejection) with diagnostic body shapes.
- Includes the programmatic probe script.
- Explicitly calibrates against the 2026-04-29 misdiagnosis.
- Names the four cause classes
  (`OK` / `CAUSE_1_CLOUDFLARE_UA` / `CAUSE_2_CREDS` / `NETWORK` /
  `OTHER`) that `hai doctor --deep` will surface.

W-AE acceptance in PLAN.md §2.B revised to cite this in-repo path
instead of the memory note. The memory note continues to exist for
my own future-session calibration but is no longer a load-bearing
project artifact; the repo doc is the canonical source.

**Edit sites:** new file `reporting/docs/intervals_icu_403_triage.md`,
§2.B W-AE acceptance section, §3 ship gates (new row for triage doc
existence).

### F-PLAN-11 — W-29-prep boundary scope stale + collides with W-AB/W-AE

**Disposition:** ACCEPT.

Three coordinated edits:

1. Subcommand count derived from manifest, not hardcoded. The "22
   subcommands" claim was both wrong (24 + 1 actual) and stale (the
   number is whatever the live parser registers at any given
   moment).
2. Capabilities byte-stability baseline frozen AFTER W-AB + W-AE
   land — those are intentional v0.1.13 surface changes that would
   produce false byte-equality regressions if W-29-prep snapshotted
   pre-cycle. Sequencing note added explicitly.
3. Ship-gate row in §3 rewritten to "deterministic against the
   post-W-AB/W-AE baseline."

This sequencing constraint is real-bug-preventing: without it, the
W-29-prep test would either (a) have to be edited every time W-AB
or W-AE shipped (bad), or (b) catch legitimate v0.1.13 surface
changes as regressions (worse).

**Edit sites:** §2.C W-29-prep contract (substantial expansion with
sequencing note), §3 ship gates capabilities row, §4 risks register
(new row for W-29-prep / W-AB+W-AE coupling).

---

## Answers to Codex's open questions

1. **W-CARRY a workstream?** Yes — has its own per-WS contract.
   PLAN updated to 17 W-ids (F-PLAN-01).
2. **W-Vb scope?** P1 + P4 + P5 in v0.1.13. P9/P11/P12 fork-deferred
   to v0.1.14 W-Vb-3 per honest partial-closure-naming convention
   (F-PLAN-06).
3. **W-FBC-2 option?** Option A default per design doc; option B as
   the only documented fork; option C explicitly out-of-v0.1.x
   scope and not reopened by this cycle (F-PLAN-07).
4. **Cherry-pick hotfix RELEASE_PROOF?** Yes — done at commit
   a10a238 on cycle/v0.1.13. In-tree provenance now honest
   (F-PLAN-03).

---

## What round 2 should re-verify (anti-self-introduced-regression)

Per the v0.1.12 D14 round-2 pattern (5 second-order findings
introduced by round-1 revisions, including W-Vb deferral not
propagating + summary-surface drift), round 2 of this audit should
specifically check:

- **Summary-surface coherence after the W-Vb-3 fork-defer.** The
  partial-closure-naming convention requires:
  (a) §1.2.A W-Vb catalogue row mentions P1+P4+P5 ship-set;
  (b) §1.3 out-of-scope has a W-Vb-3 row;
  (c) §2.A W-Vb contract acceptance lists all three ship-set
      personas;
  (d) §3 ship-gate demo-regression row references all three;
  (e) §4 risks register W-Vb row mentions P9/P11/P12 destination;
  (f) CARRY_OVER §4 has a W-Vb-3 v0.1.14 defer row.
  All six should be present after round 1 revisions. Round 2
  audit explicitly: are they all coherent or does one say "P1 only"
  and another say "P1+P4+P5"?
- **Effort-roll-up coherence.** §1.2 says 22.5-32.5d total. §5 says
  22-32d single-contributor (NOT updated yet — this is a
  potential round-2 finding). §4 risks register row says
  "5-week budget." Round 2 audit: do all three numbers reconcile?
- **F-PLAN-03 cherry-pick provenance.** PLAN §1.2.D "cherry-pick
  from hotfix/v0.1.12.1 as its first commit" — but commit 636f5d3
  is the code commit, and a10a238 is the RELEASE_PROOF doc commit.
  Round 2 should verify the wording is honest about "two cherry-
  picks," not "one." (CARRY_OVER §5 was updated; PLAN §1.2.D may
  still claim "one commit" — needs spot-check.)
- **F-PLAN-04 path prefix completeness.** Did I miss any runtime
  paths in §2 contracts? Quick grep for `core/`, `domains/`,
  `cli.py` without `src/health_agent_infra/` prefix would catch
  any I missed.
- **F-PLAN-08 onboarding_slo.md citation.** The deterministic-vs-
  operator-SLO split cites `reporting/docs/onboarding_slo.md` (new)
  — if round 2 checks for the file, it won't exist yet. PLAN
  explicitly notes the file is authored at W-AA implementation
  time, not at PLAN time. Round 2 should accept this citation
  shape OR catch it as a finding for explicit "to-be-authored at
  cycle implementation" tagging.

If any of these surface in round 2, the maintainer response
addresses them directly; this is the documented self-introduced-
regression pattern.

---

## Provenance — files modified in response to round 1

| File | Change shape | Codex finding(s) |
|---|---|---|
| `reporting/plans/v0_1_13/PLAN.md` | Multiple sections revised | F-PLAN-01, 04, 05, 06, 07, 08, 09, 10, 11 |
| `reporting/plans/v0_1_13/CARRY_OVER.md` | §2 + §4 + §5 expanded | F-PLAN-02, 03, 06 |
| `reporting/docs/intervals_icu_403_triage.md` | New file | F-PLAN-10 |
| `reporting/plans/v0_1_12_1/RELEASE_PROOF.md` | Cherry-picked into cycle/v0.1.13 (a10a238) | F-PLAN-03 |
| `reporting/plans/v0_1_13/codex_plan_audit_response_round_1_response.md` | This file | (response convention) |

All edits committed as a single commit on cycle/v0.1.13 alongside
this response. Branch state ready for D14 round 2.
