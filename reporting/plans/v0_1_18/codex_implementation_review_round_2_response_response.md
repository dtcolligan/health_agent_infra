# Maintainer Response — v0.1.18 D15 IR Round 2

**Author:** Claude (autonomous mode under maintainer ratification).
**Date:** 2026-05-06.
**IR Round 2 verdict:** SHIP_WITH_FIXES — 2 findings.
**Disposition summary:** **Both findings accepted; both fixed in
fix-and-reland-2 commit.** No rejections; no challenges. Codex's
broader walk of `core/doctor/checks.py` post-R1 closure surfaced one
missed concrete-command path (deep-probe outcomes) that R1's
enumeration didn't catch, plus the canonical R2 failure mode
(summary-surface sweep gaps that the §2 ship-gate stamp obscured).
Settling shape: **R1 4 → R2 2 → fix-and-reland-2.**

---

## Per-finding triage

### F-IR-R2-01 — Deep-probe credential-failure hints still omit `next_action` ⇒ ACCEPT

**Verified by direct reproduction.** With a credentials-present
`CredentialStore` + `ProbeResult(ok=False, outcome_class="CAUSE_2_CREDS")`,
`check_auth_intervals_icu` returned `status: "fail"`, hint pointing
at `hai auth intervals-icu`, and **no `next_action` field**. The
deep-probe failure path branches on `outcome_class` and sets
`out["hint"] = OUTCOME_NEXT_STEPS[outcome_class]`, but the F-IR-03
fix only covered the no-creds shallow branch.

The `OUTCOME_NEXT_STEPS` dict has 4 entries; 2 map to concrete
commands:

- `CAUSE_2_CREDS` → "Re-run `hai auth intervals-icu`"
- `NETWORK` → "...re-run `hai doctor --deep`"

The other 2 (`CAUSE_1_CLOUDFLARE_UA`, `OTHER`) are diagnostic prose
pointing at the triage doc, not a single concrete command — they
intentionally stay prose-only.

**Fix.** Added a small `_DEEP_PROBE_NEXT_ACTION` dict inside the
deep-probe failure branch:

```python
_DEEP_PROBE_NEXT_ACTION = {
    "CAUSE_2_CREDS": "hai auth intervals-icu",
    "NETWORK": "hai doctor",
}
command = _DEEP_PROBE_NEXT_ACTION.get(outcome_class)
if command is not None:
    out["next_action"] = _next_action(command)
```

`hai doctor` was already added to `_NEXT_ACTION_REGISTRY` at IR R1
F-IR-03 close, so no registry expansion needed for F-IR-R2-01.

**4 new regression tests** in `test_doctor_next_action.py`:

- `test_auth_intervals_icu_deep_probe_cause_2_creds_emits_next_action` — asserts CAUSE_2_CREDS → `hai auth intervals-icu`.
- `test_auth_intervals_icu_deep_probe_network_emits_next_action` — asserts NETWORK → `hai doctor`.
- `test_auth_intervals_icu_deep_probe_cause_1_stays_prose_only` — explicit "prose-only by design" for CAUSE_1.
- `test_auth_intervals_icu_deep_probe_other_stays_prose_only` — same for OTHER.

The "prose-only" pair codifies the design intent so a future cycle
can't silently change them without breaking the test.

**Lesson.** The R1 F-IR-03 enumeration was static-text-grep-based
(walked `"hint"` literal occurrences); the deep-probe branch sets
`hint` programmatically from `OUTCOME_NEXT_STEPS[outcome_class]` at
runtime, so the static walk missed it. Future enumeration of "every
hint emission" should walk both literal `"hint":` fields AND
runtime-assigned `out["hint"] = ...` patterns. Codex's R2 walk
caught what the R1 walk missed; the test surface is now durable.

### F-IR-R2-02 — Release-summary surfaces stale post-R1 fix ⇒ ACCEPT

**Verified.** Codex enumerated 7 stale surfaces:

| Surface | Stale claim | Corrected |
|---|---|---|
| `agent_integration.md:27` | "root README leads with `hai init --guided`" | now: "leads with `pipx install`, bare `hai init` (post-v0.1.18 W-OB-2: on a TTY...auto-promotes...; opt-outs are `--non-interactive`, `HAI_INIT_NON_INTERACTIVE=1`, or no TTY)" |
| `CHANGELOG.md:61-64` | W-OB-1 pivots `--guided` as recommended | now: pivots to bare `hai init`; rewritten post-IR-R1 F-IR-02; `--guided` retained as explicit-force spelling |
| `RELEASE_PROOF.md:18` | "README already shows `hai init --guided` at HEAD `9c651da`" | now: leads with bare `hai init`; F-IR-02 closure callout |
| `RELEASE_PROOF.md:20` (W-OB-3 row) | "6 new tests; hint logic based on auth + intent status" | now: 8 tests + primitive `intent_ids`/`target_ids` logic + R1 regression callout |
| `RELEASE_PROOF.md:23` (W-OB-5 row) | "9-command registry; 5 doctor checks" | now: 11 commands; 9 doctor check paths (including R1+R2 additions); deep-probe coverage; CAUSE_1+OTHER prose-only by design |
| `REPORT.md:202-204` | listed `check_today`/`check_intake_gaps`/`check_config` as "don't yet emit `next_action`" | now: CLOSED at R1 F-IR-03 + R2 F-IR-R2-01; "concrete command vs prose" rule codified |
| `current_system_state.md:48,64` | "W-OB-1...mention `--guided`" + "W-OB-5...5 hint-emitting checks" | now: bare `hai init` primary; 9 doctor check paths |

**Fix.** Text-only sweep across all 7 surfaces; no code or test
change. The fix-and-reland-2 commit's diff stat shows 5 doc files
changed (the 7 surfaces collapse to 5 files — RELEASE_PROOF has 3
distinct rows; current_system_state has 2 distinct paragraphs).

**Lesson.** This is the canonical R2 failure mode AGENTS.md
"Patterns the cycles have validated" (Summary-surface sweep on
partial closure) names: **when a fix lands, every summary surface
that describes the fixed-area state must move in lockstep.** The
R1 fix-and-reland touched code + tests + RELEASE_PROOF §2 (gates) +
REPORT §5.5/§5.6 (lessons), but missed RELEASE_PROOF §1 (per-W-id
rows), REPORT §6 (open items), CHANGELOG §"Doctrine" + §"Tests",
agent_integration.md, and current_system_state.md.

The pattern that should apply: when authoring a fix-and-reland
response_response, the file-level diff plan should explicitly walk
every summary surface, not just the canonical RELEASE_PROOF/REPORT
top-level. Or: the response_response itself should treat the
"Files modified" table as a checklist, with the maintainer ticking
each surface as the sweep lands.

For v0.1.18 specifically, the R2 sweep adds these 5 doc files to
the cumulative cycle file-modification trail. Future cycles should
treat the R1 fix-and-reland surface list as the *minimum* sweep,
not the maximum.

---

## Verification post-fix-and-reland-2

| Gate | Pre-R2 (post-R1) | Post-R2 |
|---|---|---|
| `uv run pytest verification/tests -q` | 2729 passed, 5 skipped | **2733 passed, 5 skipped** (~130s) |
| `uv run pytest verification/tests -W error::Warning -q` | 2729 passed, 5 skipped | **2733 passed, 5 skipped** (~130s) |
| `uvx mypy src/health_agent_infra` | clean | clean |
| `uvx bandit -ll -r src/health_agent_infra` | 0 medium / 0 high | 0 medium / 0 high |
| Targeted W-OB tests | 41 passed | **46 passed** (+5: 4 W-OB-5 R2 + ratification) |
| `_NEXT_ACTION_REGISTRY` manifest-consistency | green (11 entries) | green (no new entries; deep-probe additions are leaf-command lookups using existing registry rows) |

Total test surface delta vs. v0.1.17 ship: **+50 tests** (was +46
post-R1; +4 from F-IR-R2-01).

---

## Files modified in fix-and-reland-2

| File | F-IR-R2-X | Change |
|---|---|---|
| `src/health_agent_infra/core/doctor/checks.py` | F-IR-R2-01 | deep-probe failure branch sets `next_action` for CAUSE_2_CREDS + NETWORK |
| `verification/tests/test_doctor_next_action.py` | F-IR-R2-01 | +4 regression tests (2 concrete-command + 2 prose-only-by-design) |
| `reporting/docs/agent_integration.md` | F-IR-R2-02 | install lead now bare `hai init` + W-OB-2 auto-promotion + opt-outs |
| `CHANGELOG.md` | F-IR-R2-02 | W-OB-1 entry rewritten with R1 fix-and-reland callout; test-count update |
| `reporting/plans/v0_1_18/RELEASE_PROOF.md` | F-IR-R2-02 | §1 W-OB-1 / W-OB-3 / W-OB-5 rows updated with post-R1+R2 state; §2 stamped 2733 + R2 closure callout |
| `reporting/plans/v0_1_18/REPORT.md` | F-IR-R2-02 | §6 "W-OB-5 registry exhaustiveness" marked CLOSED; concrete-vs-prose rule codified |
| `reporting/docs/current_system_state.md` | F-IR-R2-02 | W-OB-1 + W-OB-5 paragraphs in §"v0.1.18 shipped" rewritten; test gate count 2733 |
| `AUDIT.md` | F-IR-R2-02 | IR R2 row stamped with 2 findings + R3 placeholder |
| `reporting/plans/v0_1_18/codex_implementation_review_round_2_response_response.md` | (this file) | new |
| `reporting/plans/v0_1_18/codex_implementation_review_round_3_prompt.md` | (handoff) | new — narrow R3 pass per Codex closure recommendation |

10 file-level changes (8 modified + 2 new).

---

## Per-W-id verdict updates (post-R2 fix-and-reland)

| W-id | R1 verdict | R2 verdict | Post-R2 status |
|---|---|---|---|
| W-OB-1 | FIX → PASS | (unchanged) | PASS |
| W-OB-2 | PASS | (unchanged) | PASS — manual TTY UX gate still required pre-publish |
| W-OB-3 | FIX → PASS | (unchanged) | PASS |
| W-OB-4a | PASS | (unchanged) | PASS |
| W-OB-4b | PASS_WITH_NOTE | (unchanged) | PASS_WITH_NOTE — substitution shape ratified |
| W-OB-5 | FIX → PASS (R1) | FIX (R2 deep-probe gap) | **PASS** — deep-probe `next_action` + 4 regression tests landed |
| W-OB-7 | PASS | (unchanged) | PASS |

---

## Round-3 expectation

Per Codex closure recommendation: "one narrow R3 pass focused on
the deep-probe branch, docs propagation, and stamped gate counts."
This response_response represents the focused fix pass; R3 prompt
authors next for the maintainer to launch.

**Author's predicted R3 finding density:** 0-1 findings. The fix-
and-reland-2 touched 1 source file + 1 test file + 6 doc files;
none introduced new W-id-class scope. The most likely R3 surface:
verification of the prose-only-by-design intent for CAUSE_1 +
OTHER (codified by the 2 negative tests, but Codex may want
explicit justification in the registry comment), or further
provenance drift between the file-modifications table here and
the actual diff (mitigated by listing 10 changes explicitly above).

---

## Round-3 prompt authoring

After this commit lands, the round-3 prompt authors at
`reporting/plans/v0_1_18/codex_implementation_review_round_3_prompt.md`.
The maintainer launches Codex against that prompt; expected verdict
SHIP or SHIP_WITH_NOTES close-in-place.
