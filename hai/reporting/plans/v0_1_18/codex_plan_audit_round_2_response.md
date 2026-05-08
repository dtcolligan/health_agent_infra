# Codex Plan Audit Response — v0.1.18 PLAN.md (D14 round 2)

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

**Round:** 2

## Findings

### F-PLAN-R2-01. Round-1 wording did not fully propagate to summary and acceptance metadata

**Q-bucket:** Q1  
**Severity:** summary-surface-sweep-gap  
**Reference:** PLAN.md §1.1 lines 40,42; §1.4 lines 88,90; §2.B line 125; §2.C lines 172,178; §4 line 383; §7 line 463; §9 lines 531-532

**Argument:** The core W-OB-4 split landed correctly in §1.2, §1.3, §2.D, §5, and §6, but several summary surfaces still describe the pre-round-1 shape. §1.1 says W-OB-4 dogfoods clean install + upgrade "against a real PyPI install" and frames the honesty boundary as "install or upgrade ... from PyPI cold"; §1.4 still says the maintainer dogfood-validates the full path "on a clean PyPI install." That contradicts §2.D lines 193 and 215-237, where W-OB-4b is explicitly a pre-ship local-wheel smoke and does not depend on a published PyPI artifact. §7 still names "v0.1.18 W-OB-4" rather than W-OB-4a / W-OB-4b, and §9 still shows "Phase 1 (W-OB-1 + W-OB-7 + W-OB-4) -> atomic Phase 1 commits" with no W-OB-4b after W-OB-2, despite §1.3 line 78 saying W-OB-4a/4b are dogfood-evidence gates, not code commits.

The same propagation issue remains for smaller round-1 edits. §2.B line 125 and §4 line 383 still say the default-flip test covers "four cases," while §2.B line 148 and §6 line 437 correctly require five cases after OQ-2. §2.C line 172 still asks what happens if the user types "skip," while §2.C line 177 correctly says W-OB-3 does not add a literal `skip` keyword and tests empty input instead. §2.C acceptance also jumps from item 2 to item 6, then back to 3-5.

**Recommended response:** Revise the stale summary surfaces only: replace pre-ship PyPI dogfood wording with local-wheel ship-gate wording plus post-publish PyPI verification in RELEASE_PROOF; replace generic W-OB-4 references with W-OB-4a / W-OB-4b where sequencing matters; update §9 to show W-OB-4a in Phase 1 and W-OB-4b after W-OB-2 in Phase 2 as evidence gates, not commits. Synchronize W-OB-2 "four cases" to five cases, change the §2.C review prompt from literal `skip` to empty/no-input refusal, and renumber §2.C acceptance.

### F-PLAN-R2-02. W-OB-7 still has stale caller/provenance details

**Q-bucket:** Q4  
**Severity:** provenance-gap  
**Reference:** PLAN.md top metadata line 3; §2.G lines 337-338; §4 lines 387,390

**Argument:** The main W-OB-7 inventory was corrected to eight handlers in §2.G and §5, but stale and misattributed details remain. The top D15 tier note still says W-OB-7 is "one shared seam, six callers," contradicting the corrected eight-handler contract at §2.G lines 308 and 344-346.

The per-handler table also misattributes the open-connection call sites. `rg -n "^def cmd_intake_|open_connection|_project_readiness_submission_into_state" src/health_agent_infra/cli/handlers/intake.py` shows `cmd_intake_readiness` starts at line 903 and calls `_project_readiness_submission_into_state` at line 958; that helper starts at line 1124 and opens the DB at line 1149. `cmd_intake_gaps` starts at line 980 and opens the DB at lines 1025 and 1093. PLAN §2.G lines 337-338 currently assigns 1025/1093 to readiness and 1149 to gaps, which reverses the actual ownership.

Risk 5 is also still written against the discarded seam shape: it refers to `connect_and_migrate` and says handlers use `with sqlite3.connect(...) as conn:` patterns. The current code uses `core.state.open_connection`, and the planned helper is named `open_connection_with_migrations`. Risk 8's aggregate line list is mostly useful, but it repeats the same unclassified `1025/1093/1149` bundle, so the table remains the source of truth that needs correction.

**Recommended response:** Change line 3 to "eight callers." In §2.G, assign readiness to the helper-backed call at 1149 and gaps to 1025/1093. Rewrite Risk 5 around `open_connection_with_migrations` preserving the existing `open_connection` return/close contract; remove `sqlite3.connect` and `connect_and_migrate` from that risk unless they are intentionally reintroduced.

### F-PLAN-R2-03. W-OB-5 runtime-only scope still conflicts with manifest and doctor-check names

**Q-bucket:** Q1  
**Severity:** summary-surface-sweep-gap  
**Reference:** PLAN.md §1.2 line 53; §2.E lines 245,276; §6 lines 429,452

**Argument:** OQ-4 is settled as "runtime check level only — NOT in the manifest" (§8 line 486), and §2.E lines 248 and 286 plus §3 line 371 correctly say W-OB-5 does not extend `hai capabilities --json`. Two downstream surfaces still contradict that. The §1.2 W-OB-5 row still says "capabilities manifest update," and the §6 capabilities gate attributes the snapshot round-trip to "W-OB-2 (new flag) + W-OB-5 (new field)." That makes W-OB-5 look like it mutates the capabilities snapshot, when the intended W-OB-5 test is only a runtime consistency check that reads the manifest to validate `next_action.agent_safe`.

The widened doctor-check scope also names non-existent or wrong-shaped checks. §2.E line 245 names `check_credentials`, but `core/doctor/checks.py` has `check_auth_garmin` and `check_auth_intervals_icu`, not `check_credentials`. §2.E line 276 says `check_onboarding_readiness` covers missing "intent / target / credentials"; the actual function documents and checks intent, target, and successful wellness pull at lines 478-481 and 530-546. Credentials belong under the auth checks, not onboarding readiness.

**Recommended response:** Remove "capabilities manifest update" from the W-OB-5 catalogue row. Change the §6 capabilities round-trip source to W-OB-2 only, with W-OB-5 mentioned separately as a runtime manifest-consistency test that reads but does not change the capabilities manifest. Replace `check_credentials` with the concrete auth-check names, or use an explicit phrase like "credential/auth checks (`check_auth_garmin`, `check_auth_intervals_icu`)." Change onboarding readiness coverage to intent / target / wellness_pull.

## Round-1-revision verification

| Revision | Status | Note |
|---|---|---|
| Rev 1 — W-OB-4 split | GAPS-FOUND | Core split is present in §1.2, §1.3, §2.D, §5, §6, and §4, but summary/cycle-position surfaces still carry PyPI and generic W-OB-4 wording. See F-PLAN-R2-01. |
| Rev 2 — W-OB-7 8 handlers | GAPS-FOUND | Eight-handler contract mostly landed, but top metadata still says six callers and the readiness/gaps call-site table is wrong. See F-PLAN-R2-02. |
| Rev 3 — W-OB-5 scope widening | GAPS-FOUND | Example uses `hai init` and `agent_safe: false`; runtime-only language exists, but catalogue/ship-gate manifest wording and check names still conflict. See F-PLAN-R2-03. |
| Rev 4 — v0.2.0 sequencing | VERIFIED | §1 metadata removes the parallelizable claim and §7 names the v0.1.18 -> v0.1.19 -> v0.2.0 chain. Tactical §5G confirms v0.2.0 depends on v0.1.19. |
| Rev 5 — W-OB-3 test file | GAPS-FOUND | Test file path is corrected to `test_init_onboarding_flow.py`, but the review-surface text still names literal `skip` and acceptance numbering is out of order. Covered under F-PLAN-R2-01. |
| Rev 6 — §6 ship gate adds | GAPS-FOUND | New W-OB-4a/W-OB-4b/W-OB-7/W-OB-5 gates are present. The capabilities round-trip row still attributes a "new field" to W-OB-5, conflicting with OQ-4. See F-PLAN-R2-03. |
| Rev 7 — OQ dispositions | GAPS-FOUND | §8 records all seven dispositions, but OQ-2 and OQ-4 did not fully propagate to §2.B/§4 and §1.2/§6 respectively. See F-PLAN-R2-01 and F-PLAN-R2-03. |

## Closure recommendation

PLAN is coherent after a targeted text/provenance revision pass. The must-fix list is:

1. Apply F-PLAN-R2-01's summary-surface cleanup for W-OB-4a/W-OB-4b, W-OB-2 five-case wording, and W-OB-3 refusal wording/numbering.
2. Apply F-PLAN-R2-02's W-OB-7 caller-count, readiness/gaps call-site, and risk-register seam-shape corrections.
3. Apply F-PLAN-R2-03's W-OB-5 runtime-only manifest wording and concrete doctor-check-name corrections.

Recommended next-round budget: close-in-place after the PLAN-author patches these exact textual issues and records the disposition. A full D14 round 3 is not necessary unless the revision changes scope or introduces new acceptance semantics.
