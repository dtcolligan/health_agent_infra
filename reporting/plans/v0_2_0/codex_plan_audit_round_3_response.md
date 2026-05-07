# Codex Plan Audit Response — v0.2.0 PLAN.md (R3)

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

**Round:** 3 / 4

## Findings (R3)

### F-PLAN-R3-01. Comparative-claim scope did not propagate to all summary surfaces

**Q-bucket:** Q1 / Q2
**Severity:** stale-propagation
**Reference:** `PLAN.md` §0 theme, line 13; `PLAN.md` §2.A, lines 201 and 203; `PLAN.md` §3.4, line 676; `PLAN.md` §6, line 785
**Argument:** F-PLAN-R2-01 fixed the stale "every atomic claim" wording, but a narrower stale phrasing remains: several summary surfaces still say only "quantitative claim(s)." The revised cycle thesis and W52 acceptance now cover quantitative **and comparative** factual atoms. This matters most for W-PROV-2 partial closure: deferred-domain suppression must suppress comparative claims too, not only numeric claims.
**Recommended response:** Update these remaining surfaces to "quantitative or comparative factual claim(s)" / "quantitative and comparative claims." In particular, line 203 and line 676 should say W52 suppresses quantitative **and comparative** claims for deferred domains.

### F-PLAN-R3-02. Canonical-latest and `--include-history` did not reach all command/output surfaces

**Q-bucket:** Q1 / Q2
**Severity:** stale-propagation
**Reference:** `PLAN.md` §2.C, line 313; `PLAN.md` §2.D, lines 341-348, 415, and 417
**Argument:** F-PLAN-R2-03 added canonical-latest default output and a new `--include-history` flag. §2.D acceptance #9 and #11 carry the fix, but §2.C acceptance #5 still says `hai review weekly --json` includes one entry "per card" for the requested week, which reads as all append-only rows rather than canonical-latest rows. The CLI surface block also still lists only `--week`, `--json|--markdown`, `--user-id`, and `--coverage-threshold`; it omits `--include-history` even though acceptance #11 says four flags.
**Recommended response:** Revise §2.C acceptance #5 to say default JSON emits the canonical-latest `claim_cards` view, with full append-only history only under `--include-history`. Add `[--include-history]` to the CLI surface block and clarify it is valid with `--json`.

### F-PLAN-R3-03. G2 test-count target has three unallocated tests

**Q-bucket:** Q3
**Severity:** nit
**Reference:** `PLAN.md` §3.1 G2, line 630
**Argument:** G2 sets the full-suite growth target at `≥ v0.1.18 + 86`, but the visible per-workstream projection sums to 83: W-PROV-2 +6, W-EVCARD-DAILY +12, W-EVCARD-WEEKLY +8, W52 +23, W-FACT-ATOM +8, W58D +26. The line says "others minor," but does not allocate the remaining +3 to any workstream or gate. The threshold may be intentionally conservative, but the arithmetic is not fully auditable.
**Recommended response:** Either lower G2 to `≥ v0.1.18 + 83`, or keep `+86` and explicitly name the extra +3 tests (for example doc-freshness/capabilities/ship-gate assertions) so the count can fail cleanly.

## Open questions for maintainer

None.
