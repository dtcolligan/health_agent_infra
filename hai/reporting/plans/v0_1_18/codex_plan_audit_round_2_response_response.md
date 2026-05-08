# Maintainer Response — v0.1.18 D14 Round 2

**Author:** Claude (autonomous mode under maintainer ratification).
**Date:** 2026-05-06.
**Round 2 verdict:** PLAN_COHERENT_WITH_REVISIONS — 3 findings.
**Disposition summary:** **All 3 findings accepted; PLAN revised in lockstep.** Close-in-place per Codex closure recommendation; no D14 round 3 needed unless this revision pass introduces new scope (it does not — text/provenance corrections only).
**Settling shape:** **7 → 3** matches the AGENTS.md empirical norm `10 → 5 → 3 → 0` halving signature. Round 2 caught exactly the predicted failure mode (summary-surface-sweep gaps); no second-order contradictions emerged.

---

## Per-finding triage

### F-PLAN-R2-01 — Round-1 wording didn't fully propagate ⇒ ACCEPT

**Verified.** Codex catalogued the unmoved surfaces precisely:

- §1.1 line 40 + §1.4 line 88-90: still say "PyPI install" / "PyPI cold" — should be "locally built wheel" pre-ship + post-publish PyPI verification deferred to RELEASE_PROOF.
- §2.B line 125 + §4 line 383: still say "four cases" — should be "five cases" per OQ-2.
- §2.C lines 172/178: still ask about literal `skip` — should be "empty / no input."
- §2.C acceptance numbering: jumps 2 → 6 → 3-5 because round-1 inserted item 6 mid-list without renumbering.
- §7 line 463: still says "v0.1.18 W-OB-4" without the 4a/4b split.
- §9 line 531-532 cycle-position diagram: Phase 1 still lists "W-OB-4"; no Phase 2 W-OB-4b after W-OB-2.

**Revisions to PLAN:** corrections to all 8 surfaces. Text-only; no scope shift.

### F-PLAN-R2-02 — W-OB-7 stale caller/provenance details ⇒ ACCEPT

**Verified.** Two material misattributions:

1. **Top D15 tier annotation line 3:** "one shared seam, six callers." Should be "eight callers" — the per-handler table at §2.G already says eight; the tier annotation is the single remaining instance of the stale count.
2. **§2.G per-handler table readiness/gaps swap.** Verified on disk: `cmd_intake_readiness` (line 903) calls `_project_readiness_submission_into_state` at line 958; that helper (defined at 1124) opens the DB at line 1149. `cmd_intake_gaps` (line 980) opens connections at lines 1025 (presence) + 1093 (write). PLAN currently assigns these backwards — readiness=1025/1093, gaps=1149. Swap.
3. **Risk 5** still references `connect_and_migrate` (the old proposed seam name, now `open_connection_with_migrations`) and `with sqlite3.connect(...) as conn:` (the wrong seam shape — handlers use `core.state.open_connection`).

**Revisions to PLAN:** correct top-line caller count; swap readiness/gaps line numbers in §2.G table; rewrite Risk 5 around `open_connection_with_migrations` + `open_connection`.

### F-PLAN-R2-03 — W-OB-5 runtime-only scope conflicts with manifest + check-name wording ⇒ ACCEPT

**Verified.** Two distinct sub-issues:

1. **Manifest contradiction.** §2.E lines 248 + 286 + §3 correctly say W-OB-5 is runtime-only (no `hai capabilities --json` extension). But §1.2 W-OB-5 catalogue row still says "capabilities manifest update" and §6 "capabilities round-trip" gate still attributes "new field" to W-OB-5. Both contradict OQ-4.
2. **Check-name fabrication.** `check_credentials` doesn't exist on disk; actual checks are `check_auth_garmin` (line 155) and `check_auth_intervals_icu` (line 190). And `check_onboarding_readiness` (line 470) covers intent / target / **wellness_pull** (per docstring lines 479-481 + logic at 530-546), not "credentials." The PLAN-author confused intervals.icu credentials (an *auth* check) with onboarding readiness (an intent/target/wellness check).

**Revisions to PLAN:** drop "capabilities manifest update" from §1.2 W-OB-5 row; change §6 capabilities gate source to W-OB-2 only with W-OB-5 noted as a runtime *consumer* of the manifest, not a producer; replace `check_credentials` with `check_auth_garmin` + `check_auth_intervals_icu`; correct onboarding_readiness coverage to "intent / target / wellness_pull."

---

## Round-1-revision verification ratification

Codex's table accepted as-is:

| Revision | Status | Note |
|---|---|---|
| Rev 1 — W-OB-4 split | GAPS-FOUND → fixed via F-PLAN-R2-01 | Core split landed; summary surfaces not propagated |
| Rev 2 — W-OB-7 8 handlers | GAPS-FOUND → fixed via F-PLAN-R2-02 | Eight-handler contract landed; top-line + per-handler-table + risk 5 stale |
| Rev 3 — W-OB-5 scope widening | GAPS-FOUND → fixed via F-PLAN-R2-03 | Example correct; catalogue + ship-gate + check-name still stale |
| Rev 4 — v0.2.0 sequencing | VERIFIED | No further action |
| Rev 5 — W-OB-3 test file | GAPS-FOUND → fixed via F-PLAN-R2-01 | Test path corrected; review-surface text + numbering not |
| Rev 6 — §6 ship gate adds | GAPS-FOUND → fixed via F-PLAN-R2-03 | New gates landed; capabilities round-trip still mis-attributes W-OB-5 |
| Rev 7 — OQ dispositions | GAPS-FOUND → fixed via F-PLAN-R2-01 + R2-03 | All 7 in §8; OQ-2 + OQ-4 propagation incomplete |

---

## Closure verdict

**Settling at round 2** per Codex closure recommendation: "PLAN is coherent after a targeted text/provenance revision pass... A full D14 round 3 is not necessary unless the revision changes scope or introduces new acceptance semantics."

**Verdict at this revision pass:** **PLAN_COHERENT close-in-place.** The R2 corrections are text-only — no scope shift, no new acceptance semantics, no new W-id, no new ship gate. The cycle opens with Phase 0 (D11) bug-hunt next.

**Tier ratification unchanged:** substantive on the W-OB-2 release-blocker leg.

**Audit-chain settling shape:** R1 7 findings → R2 3 findings → R2-close. Matches the empirical `10 → 5 → 3 → 0` norm; v0.1.18 tracks the lower density of cycles with established source contracts (the v0.1.13 W-AA mechanism + the v0.1.17 schema-add provenance), as predicted at PLAN-author time.

---

## Next steps in the cycle

1. **PLAN.md revisions land** in lockstep with this response_response (this session).
2. **D14 closes at round 2** — no round 3.
3. **Phase 0 (D11) bug-hunt opens** — internal sweep + audit-chain probe + persona matrix; optional Codex external bug-hunt audit.
4. **Pre-implementation gate** fires after `audit_findings.md` consolidates (F-OB-PRE-01 already filed; new findings append).
5. **Phase 1 implementation** (W-OB-1 → W-OB-7 → W-OB-4a) commits.
6. **Phase 2 implementation** (W-OB-3 → W-OB-2 → W-OB-4b → W-OB-5) commits.
7. **D15 IR** post-implementation; expected 2-3 rounds settling at SHIP / SHIP_WITH_NOTES.
8. **RELEASE_PROOF.md + REPORT.md** authored; v0.1.18 ships to PyPI.
9. **v0.1.19 cycle opens** — foreign-user empirical session against the post-v0.1.18 PyPI build.
