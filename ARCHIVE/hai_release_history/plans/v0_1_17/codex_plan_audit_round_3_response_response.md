# Codex Plan Audit Response-Response — v0.1.17 PLAN.md, round 3

**Round:** 3
**Verdict (Codex):** PLAN_COHERENT_WITH_REVISIONS, **3 round-3 findings** (F-PLAN-R3-01..03), close in place — **no round 4 scheduled**.
**Halving signature:** **11 → 5 → 3** matches AGENTS.md empirical norm `10 → 5 → 3 → 0`. Twice-validated v0.1.11/v0.1.12 + thrice-validated now (v0.1.14/v0.1.15/v0.1.17).
**D14 closure:** confirmed at round 3 close per Codex recommendation. **No round 4 needed.** Phase 0 (D11) bug-hunt opens next per AGENTS.md substantive-cycle pattern.

**Triage summary.** All 3 round-3 findings AGREED. Zero rejected, zero deferred. All are nit-class / close-in-place text edits.

**Audit-craft note.** Round 3 surfaced exactly the third-order class the empirical signature predicts: round-2 revisions left (a) classifier-contract details that contradict the verified runtime API (F-PLAN-R3-01: `protein_sufficiency_band="adequate"` should be `"met"` per the actual band vocabulary; §4 risk 6 prose still names the retired `cmd_synthesize`/`cmd_state_snapshot` call sites; PLAN never names `ClassifiedNutritionState` + `_nutrition_classified_to_dict` as the projected-field surface); (b) per-WS ship-gate item-ranges that didn't keep up with round-2 acceptance-item additions (F-PLAN-R3-02); (c) round-status / OQ wording that still referenced "round 2 pending" in README + §8 (F-PLAN-R3-03). All three are single-pass text edits with no new workstream / no new test surface / no new governance question.

**Verifications below executed via grep / read against HEAD `df6a13c`. No tests run, no code changed (per audit-prompt constraint).**

---

## F-PLAN-R3-01 — W-D arm-2 stale classifier-contract details

**Verdict:** AGREED, applied. Three sub-fixes.

**Verification.**

1. **Protein band vocabulary.** `domains/nutrition/classify.py:86`:
   ```python
   ProteinSufficiencyBand = str  # "met"|"low"|"very_low"|"unknown"
   ```
   The vocabulary is `met / low / very_low / unknown` — **`"adequate"` is not a valid band value**. PLAN §2.I acceptance item 2 asserted `protein_sufficiency_band="adequate"` — would fail the test for the wrong reason. Codex right.

2. **§4 risk 6 prose drift.** §4 risk 6 still reads "specifies new helper `core/target/store.py::get_active_macro_targets()` + threshold-override at `cmd_synthesize` / `cmd_state_snapshot` call sites" — that's the round-1 wording that round-2 §2.I (per F-PLAN-R2-01) explicitly retired. The corrected shape is `build_snapshot()` internal merge; CLI handlers are unchanged. Round-2 caught this in §2.I but didn't propagate to §4 risk 6. Codex right.

3. **`ClassifiedNutritionState` + serializer surface.** `grep -nE "ClassifiedNutritionState|_nutrition_classified_to_dict" src/health_agent_infra/`:
   - `domains/nutrition/classify.py:94` — `class ClassifiedNutritionState:` (frozen dataclass).
   - `core/state/snapshot.py:942` — `nutrition_block["classified_state"] = _nutrition_classified_to_dict(nutrition_classified)`.
   - `core/state/snapshot.py:1183` — `def _nutrition_classified_to_dict(classified: Any) -> dict[str, Any]:`.
   PLAN §2.I says `projected_eod_*` fields are "emitted in the classified state" but never names the dataclass or the serializer. Without explicit naming, an implementer might add the fields to a local variable inside `classify_nutrition_state()` (the function-level return) without adding them to the dataclass schema OR the serializer — meaning the fields wouldn't appear in `build_snapshot(...).nutrition.classified_state`, just in the in-process classifier object. Codex right.

**Action.**

1. **§2.I acceptance item 2 protein band correction.** `protein_sufficiency_band="adequate"` → `protein_sufficiency_band="met"`. With protein-ratio at projection = 1.0 and the v1 default `low_max_ratio=1.0`, `_classify_protein_sufficiency()` returns `"met"` (the boundary lands in the higher / more-met band per the existing ratio-band convention).

2. **§4 risk 6 prose updated.** Replaced "threshold-override at `cmd_synthesize` / `cmd_state_snapshot` call sites" with "build_snapshot internal merge per F-PLAN-R2-01 round-2 fix." CLI handlers not named (consume `build_snapshot()` output unchanged).

3. **§2.I files-of-record + acceptance item 2 explicit dataclass + serializer naming.** Added two file paths to "Files of record":
   - `src/health_agent_infra/domains/nutrition/classify.py` — already listed; clarified that the change is to the `ClassifiedNutritionState` dataclass at `:94` (gain 4 new optional fields: `projected_eod_kcal`, `projected_eod_protein_g`, `projected_eod_carbs_g`, `projected_eod_fat_g`).
   - `src/health_agent_infra/core/state/snapshot.py` — already listed; clarified that the change is to `_nutrition_classified_to_dict()` at `:1183-1209` (serialize the 4 new fields when present; omit when None for non-arm-2 paths).
   Acceptance item 2 extended: "Asserts the new fields are present in `build_snapshot(...).nutrition.classified_state` (i.e., flowed through the serializer), not only in the function-level classifier return."

---

## F-PLAN-R3-02 — §6 cites pre-round-2 acceptance item ranges

**Verdict:** AGREED, applied.

**Verification.**

PLAN §6 W-AI-2-specific gates:
- "§2.D acceptance commit-gate items 1-6 all pass at W-AI-2 commit time" → should be **1-7** post-round-2 (item 7 added: snapshot regeneration lockstep).

PLAN §6 W-B-specific gates:
- "§2.H acceptance items 1-6 all pass" → should be **1-7** post-round-2 (item 7 added: snapshot regeneration lockstep).

Round-2 added the items in §2 but didn't sweep §6's gate-text item ranges. Pure renumber drift.

**Action.**

§6 W-AI-2-specific gate updated: `1-6` → `1-7`, with "(including snapshot regeneration lockstep at item 7)" appended.

§6 W-B-specific gate updated: `1-6` → `1-7`, with "(including snapshot regeneration lockstep at item 7)" appended.

§6 F-PV14-02-specific gate already correct (no item-range citation; "items 1-5 all pass" matches the existing 5-item §2.G acceptance — item 5 was expanded in-place at round 2, not added).

---

## F-PLAN-R3-03 — Round-status + OQ prose stale

**Verdict:** AGREED, applied. **OQ-5 / OQ-6 / OQ-8 closed at this round 3** per Codex round-3 disposition + maintainer auto-mode acceptance (no escalation needed; the resolved-shape revisions from round 2 ratify cleanly).

**Verification.**

- `reporting/plans/v0_1_17/README.md:3` says "PLAN.md authored 2026-05-04 (D14 round 1 closed PLAN_COHERENT_WITH_REVISIONS, 11 findings; round 2 pending)" — stale (round 2 closed, round 3 closed, D14 closing in place).
- PLAN §8 subheading: "Carrying to round 2:" — stale.
- PLAN §8 OQ-5: "Round 2 maintainer ratification expected" — stale.
- PLAN §8 OQ-8: "Round 2 maintainer ratification expected" — stale.
- PLAN §2.I OQ-5 reference: "carries forward to round-2 maintainer ratification" — stale.

**Action.**

1. **README line 3 updated.** "round 2 pending" → "round 1 closed PLAN_COHERENT_WITH_REVISIONS (11 findings); round 2 closed PLAN_COHERENT_WITH_REVISIONS (5 findings, halving signature on track); round 3 closed PLAN_COHERENT_WITH_REVISIONS close-in-place (3 findings); D14 closed."
2. **§8 subheading + OQ-5/8 prose updated.** "Carrying to round 2" → "Carrying to round 3 (round 3 closes OQ-5/6/8; OQ-1 holds to W-29 Phase 1 close)." OQ-5 + OQ-8 closures land at round 3 per Codex disposition.
3. **§8 OQ-5 closed at round 3.** Removed from active list; added to "Closed at round 3" prefix block. Disposition: target-anchored ratified per Codex round-3 opinion ("Target-anchored default is coherent; linear extrapolation remains reachable through the full-tree projection_mode override once the wording nits are fixed" — wording nits fixed at this round-3 close).
4. **§8 OQ-6 closed at round 3.** Removed from active list. Disposition: 20/domain + 12-15 synthesis ratified per Codex round-3 opinion ("The 20/domain + 12-15 synthesis target is acceptable, and the 100% eval gate now matches the existing CLI").
5. **§8 OQ-8 closed at round 3.** Removed from active list. Disposition: 3-commit series ratified per Codex round-3 opinion ("The 3-commit default plus per-commit acceptance items 4-7 is clear, and the do-not-split branch now halts for re-authoring").
6. **§8 OQ-1 carries forward.** Per Codex: "Keep open until W-29 Phase 1 boundary refresh." This is no longer a D14 question — it's a Phase 1 implementation decision that lands when the refreshed boundary note (§2.A acceptance item 1) is authored. §8 retains OQ-1 with the Phase 1 destination explicit.
7. **§2.I OQ-5 reference updated.** "carries forward to round-2 maintainer ratification" → "ratified at round 3 close (D14 closing); target-anchored is v1 default."

---

## OQ disposition table (round-3 final close)

| OQ | Final disposition | Note |
|---|---|---|
| OQ-1 | **Open → W-29 Phase 1 close** | No longer a D14 question. Decided when refreshed boundary note (§2.A acceptance item 1) lands. |
| OQ-2 | Closed at round 1 | User state dir per Codex round-1 opinion. |
| OQ-3 | Closed at round 1 | `agent_safe=False`, user-authored-only per F-PLAN-09. |
| OQ-4 | Closed at round 1 | Append per Codex round-1 opinion. |
| OQ-5 | **Closed at round 3** | Target-anchored ratified; linear-extrapolation reachable via full-tree threshold override. |
| OQ-6 | **Closed at round 3** | 20/domain + 12-15 synthesis distribution ratified; 100% eval gate matches CLI contract. |
| OQ-7 | Closed at round 1 | Stay on existing `expected.policy.forced_action` contract; no harness extension. |
| OQ-8 | **Closed at round 3** | 3-commit series default ratified; per-commit acceptance items 4-7 explicit; halt-and-re-author branch operational. |

§8 final list at D14 close: **OQ-1 only** (carries to W-29 Phase 1).

---

## D14 cycle close

**Empirical settling (thrice-validated):**
- v0.1.11: 10 → 5 → 3 → 0 (4 rounds)
- v0.1.12: 10 → 5 → 3 → 0 (4 rounds)
- v0.1.14: 12 → 7 → 3 → 1-nit (4 rounds, similar)
- v0.1.15: 12 → 7 → 3 (3 rounds + post-Phase-0 round 4)
- **v0.1.17: 11 → 5 → 3 (3 rounds, close-in-place at round 3)** — the cleanest signature yet; the cycle settles one round earlier than v0.1.11/v0.1.12 because most catalogue rows had established source contracts in prior release-proofs (per the round-1 prompt's prediction "v0.1.17 expectation 2-3 rounds").

**Next phase per AGENTS.md substantive-cycle pattern:**

```
Pre-PLAN-open:
  [D14 round 1] CLOSED 2026-05-04 (11 findings)        ✓
  [D14 round 2] CLOSED 2026-05-04 (5 findings)         ✓
  [D14 round 3] CLOSED 2026-05-05 close-in-place (3)   ✓
  → D14 closed; PLAN.md ratified for cycle open

Phase 0 (D11): ← next
  Internal sweep
  Audit-chain probe
  Persona matrix (12 personas; baseline pre-W-Vb-4)
  Codex external bug-hunt audit (optional per maintainer)
  → audit_findings.md consolidates

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle (Phase 1 W-29 + W-30 commit first)
```

**No round 4 prompt authored.** Codex's round-3 closure recommendation explicitly stated "After applying them, the maintainer can close D14 round 3 without scheduling round 4." All three round-3 fixes are single-pass text edits with no new test surface. Round 4 would only fire if the round-3 fixes themselves introduced fourth-order issues — extremely unlikely given the fixes are line-level corrections, not structural rewrites.

---

## Change-set summary

| File | Action |
|---|---|
| `reporting/plans/v0_1_17/PLAN.md` | 3 finding-driven revisions: §2.I item 2 protein band correction; §4 risk 6 prose updated to build_snapshot internal-merge; §2.I files-of-record + item 2 explicit ClassifiedNutritionState + _nutrition_classified_to_dict naming; §6 W-AI-2 + W-B item-range 1-6 → 1-7; §8 subheading + OQ-5/6/8 closed; §2.I OQ-5 reference updated; §9 round-3 close entry. |
| `reporting/plans/v0_1_17/README.md` | Round-status line 3 updated to reflect D14 close. |
| `reporting/plans/v0_1_17/codex_plan_audit_round_3_response_response.md` | This file. |

**No round 4 prompt.** Cycle moves to Phase 0 next.

**Provenance.** This response-response authored 2026-05-05 against HEAD `df6a13c`. PLAN + README revisions land in this same edit pass; no separate commit yet (Phase 0 hasn't opened — implementation does not begin until pre-implementation gate fires post-Phase 0).
