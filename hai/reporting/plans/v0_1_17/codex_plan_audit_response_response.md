# Codex Plan Audit Response-Response — v0.1.17 PLAN.md, round 1

**Round:** 1
**Verdict (Codex):** PLAN_COHERENT_WITH_REVISIONS, 11 findings (10 must-fix + 1 close-in-place).
**Halving signature.** Round 1 returned 11 findings; AGENTS.md empirical norm is `10 → 5 → 3 → 0`. Within-norm. Round 2 budget per Codex closure recommendation: one focused round on the revised surfaces only.

**Triage summary.** All 11 findings AGREED. Zero rejected, zero partial, zero deferred.

**Audit-craft note.** Codex caught one genuine plan-craft bug (F-PLAN-01 mathematical inconsistency in W-D arm-2 projection formula + missing target-value plumbing path), three eval-substrate harness-coupling oversights (F-PLAN-02, F-PLAN-03, F-PLAN-04 all in the same cluster — acceptance items written against fields/harnesses that don't exist), two W-29 acceptance-bite tightenings (F-PLAN-05 + F-PLAN-06), one provenance-discipline cleanup (F-PLAN-08 — source docs the PLAN cites have stale 9217 LOC + v0.1.16 precondition), one capabilities-snapshot ordering inconsistency (F-PLAN-07), one W-B agent_safe semantic contradiction (F-PLAN-09), one AGENTS.md provenance-preservation note (F-PLAN-10), and one D15 tier-sentence nit (F-PLAN-11). The verifications below ran without test execution per the audit-prompt constraint.

---

## F-PLAN-01 — W-D arm-2 target-value plumbing + formula contradiction

**Verdict:** AGREED, applied.

**Verification.**

Mathematical check (Python repl): with `intake_so_far=1344`, `target=3100`, the round-1 PLAN's formula
```
remaining_day_fraction = (target - intake_so_far) / target = 1756/3100 = 0.5665
projected = intake_so_far + (target - intake_so_far) * remaining_day_fraction
        = 1344 + 1756 * 0.5665 = 2338.69
```
yields **2338.69**, not 3100. The acceptance test's assertion `projected_eod_kcal == target_kcal == 3100` cannot pass against the round-1 formula. Real bug.

Plumbing check: `core/intake/presence.py:163-213` `compute_target_status()` returns `Literal["present", "absent", "unavailable"]` — the enum string only, no target values. `domains/nutrition/classify.py:361-393` reads `calorie_target_kcal` / `protein_target_g` / `hydration_target_l` from `t["classify"]["nutrition"]["targets"]` (thresholds config), not from any `target` table row. Confirmed: there is no data path between committed `target` rows and the nutrition classifier in the v0.1.15.1 tree.

**Action.** §2.I rewritten end-to-end:

1. **Plumbing path.** Adopted Codex's third option (threshold-override at call site), which matches AGENTS.md D13 trusted-by-design seam — `classify_nutrition_state` already accepts `thresholds: Optional[dict]`. New section in §2.I "Plumbing path" specifies: a new helper `core/target/store.py::get_active_macro_targets(conn, user_id, as_of)` reads the four active macro rows from `target` (post-migration 025) and returns a `dict[str, float]` (kcal, protein_g, carbs_g, fat_g). The `cmd_synthesize` / `cmd_state_snapshot` call site, when `target_status == "present"`, calls this helper and passes the values as a thresholds override to `classify_nutrition_state`. Classifier code is unchanged at the function-body level; the override flows through the existing D13 seam.

2. **Formula.** Replaced the broken `remaining_day_fraction` derivation with the simpler target-anchored shape: when `is_partial_day == true && target_status == "present"`, the runtime emits `projected_eod_kcal = target_kcal` and `projected_eod_protein_g = target_protein_g` (and same for carbs / fat). The projection IS the target — the assumption is "user closes the gap by end of day." Calorie balance evaluates against the projection, which means deficit = 0 and the band fires `aligned` cleanly. **Linear-extrapolation** (rejected default per OQ-5) is named in §2.I + §4 risk 6 as the alternative, with the trade-off explicit.

3. **Macro projection scope.** §2.I now specifies that all four macros (calories, protein, carbs, fat) are projected; hydration is held observed in v1 (no hydration target in the W-C-shipped 4-row group, and W-A's `target_status="present"` is defined over the four macro rows only).

4. **Acceptance items rewritten** (5 → 7) to assert the target-row lookup, the projection emission, and the classified-band outcome separately. Specifically:
   - Item 1 now asserts `get_active_macro_targets()` returns the seeded values + the projection helper emits `projected_eod_kcal == 3100` + `nutrition_status == "aligned"` against the projection.
   - Item 2 asserts the absent / unavailable cases fall through to W-D arm-1 unchanged.
   - Item 3 asserts the day-closed case falls through to existing classifier (no projection).
   - Item 4 asserts the linear-extrapolation alternative is reachable via threshold override (allows a future flip without re-touching the classifier).
   - Item 5 asserts `hai explain` rendering shows both observed and projected.
   - Items 6 + 7 cover synthesis-policy integration + multi-macro coverage.

5. **OQ-5 rewritten.** Now reads "ratify target-anchored as v1 default; linear-extrapolation reachable via threshold override; flip via dogfood evidence in v0.1.18+." Codex's round-1 disposition was "do not ratify until F-PLAN-01 fixed" — F-PLAN-01 is now fixed; OQ-5 stays open for round-2 maintainer ratification.

**Cross-doc fan-out (per AGENTS.md "Summary-surface sweep").**
- §1.2 catalogue Title cell unchanged (still "Partial-day nutrition end-of-day projection").
- §1.3 Phase 3 row unchanged.
- §4 risk 6 rewritten to reflect the corrected formula + the macro projection scope.
- §5 effort table W-C-EQP unchanged; W-D arm-2 unchanged at 2-3 days (the plumbing helper is small + the formula is now simpler, not larger).
- §6 ship gates unchanged.
- §8 OQ-5 rewritten as above.

---

## F-PLAN-02 — Scenario fixture/harness contract mismatch

**Verdict:** AGREED, applied.

**Verification.**

`evals/runner.py:71-86` confirms scenario loading requires `scenario_id`, `kind`, `description`, `expected`. Scoring at `:300-380` reads `expected.classified` and `expected.policy.forced_action` / `expected.policy.fired_rule_ids`. No `expected_*_token` or `expected_escalate_token` consumer.

Existing tagged fixtures: `src/health_agent_infra/evals/scenarios/recovery/rec_004_should_escalate_compound_signals.json:35` and `running/run_004_should_escalate_acwr_max.json:25` — both use singular `"tag": "w-am-adversarial-escalate"`, not `tags: [...]`.

**Action.** §2.C and §2.E acceptance items rewritten to align with the executable contract:

- §2.C item 3: was "Scenario tag taxonomy (per-scenario `tags` array)..." → now "Scenario tag (per-scenario `tag` field, singular per the v0.1.14-shipped fixture convention)..."
- §2.C item 2: was "every new scenario fixture passes its own `expected_*_token` assertion" → now "every new scenario fixture's `expected.classified` + `expected.policy` blocks pass against the live runtime via `hai eval run --scenario-set all` (or per-domain). Fixtures that fail their own expected blocks are dropped + logged, not silently shipped."
- §2.E item 2: was "Each fires its expected escalate token... asserted by an `expected_escalate_token` field" → now "Each fires its expected escalate forced-action via `expected.policy.forced_action` (matches the v0.1.14-shipped escalate fixtures' contract). Validated by the existing scenario-runner harness (`evals/runner.py:300-380`); no harness extension required."
- §2.E "Workflow" + acceptance item 3 also rewritten to drop `expected_escalate_token` references.
- §2.C "What this WS does NOT do" gains a new bullet: "Does not extend the scenario-runner harness contract or fixture schema; aligns to existing `expected.classified` + `expected.policy` shape + singular `tag` field."

**OQ-7 disposition.** Codex round-1 OQ-7: "If the plan stays on the current `expected.policy` contract, no new helper is required." Plan now stays on the current contract → OQ-7 closed in §8 as "stay on current contract; no harness extension." Removed from the open-questions list.

---

## F-PLAN-03 — Persona-matrix gate not connected to scenario corpus

**Verdict:** AGREED, applied.

**Verification.**

`verification/dogfood/runner.py` runs persona specs through CLI workflows (intake / synthesize / today / explain). `evals/cli.py:141-158` `cmd_eval_run --scenario-set all` fans out the six-domain + synthesis fixtures (excluding judge_adversarial per `:185-193`). The two are independent code paths — persona runner does not consume `evals/scenarios/`, and `hai eval run` does not consume persona specs.

**Action.** §2.C acceptance + §4 risk 7 rewritten:

- §2.C item 5: was "Persona-matrix replay against the post-W-AH-2 corpus: no new test failures vs the pre-W-AH-2 baseline run" → now "**eval-corpus replay**: `hai eval run --scenario-set all` (post-W-AH-2 tree) returns ≥95% pass-rate against fixture `expected.classified` + `expected.policy` blocks. New test surface: `test_scenario_corpus_coverage.py` asserts per-domain count floor (≥20 except synthesis ≥12); separate from the runner pass-rate assertion."
- §6 ship gates: persona matrix retained as standard substantive-cycle ship gate (independent of W-AH-2). New gate added: "`hai eval run --scenario-set all` returns ≥95% pass-rate against the post-W-AH-2 corpus."
- §4 risk 7 rewritten: previously claimed persona-matrix runtime expansion driven by scenario corpus growth — that mechanism doesn't exist. Replaced with the actual mechanism: `hai eval run` runtime grows with corpus size; document the new runtime in REPORT.md if it materially exceeds the v0.1.14 baseline.

---

## F-PLAN-04 — W-AI-2 sequencing-vs-acceptance contradiction

**Verdict:** AGREED, applied.

**Action.** Split W-AI-2's acceptance into two gates per Codex's recommendation:

- **Commit gate** (W-AI-2 itself): `hai eval review list` returns whatever corpus exists at W-AI-2 commit time (judge_adversarial corpus + whatever W-AH-2/W-AM-2 fixtures have already landed). Filter / tag / dismiss / export round-trip works against the at-commit corpus.
- **§6 ship gate**: at end of cycle, `hai eval review list --corpus all` returns the post-W-AH-2 expansion (132+) + W-AM-2 escalate fixtures (6 of 6) + the 31 judge_adversarial fixtures. Verified at ship-time, not at W-AI-2 commit-time.

§2.D acceptance item 1 rewritten accordingly. §1.3 Phase 2 sequencing note clarified: "W-AI-2 commits independently; final ship gate verifies post-W-AH-2/W-AM-2 corpus visibility."

---

## F-PLAN-05 — W-29 pre-flight not gated, abort path only covers LOC overflow

**Verdict:** AGREED, applied.

**Action.**

§2.A acceptance items expanded 8 → 10:

- **New item 1** (was prose-only "Pre-flight" section): "Refreshed boundary note authored at `reporting/plans/v0_1_17/w29_boundary_refresh.md` before the split commit series begins. Required content: current command inventory (cross-checked against `hai capabilities --json`), per-handler estimated LOC against current `cli.py` (9927 LOC), shared-helper extraction list, contested groupings, explicit `split` / `split-with-revisions` / `do-not-split` verdict per the v0.1.13 boundary-table convention."
- **New item 2** (was implicit): "If the refreshed verdict is `do-not-split`, halt the cycle. Re-author PLAN §2.A through D14 round 2+ before resuming. The cycle does NOT silently degrade to no-op."
- Renumbered original items 1-8 → 3-10.

§4 risk 1 rewritten to cover the `do-not-split` abort case explicitly: "If the refreshed boundary note returns `do-not-split` (e.g., hidden cross-handler shared state pattern that prevents clean separation), the cycle halts; PLAN §2.A re-shapes through D14; v0.1.17 ships the rest of the catalogue (Phases 2 + 3) without the W-29 split — release-blocker status converts to `fork-deferred → v0.1.18+ W-29-3` per AGENTS.md 'Honest partial-closure naming.'" This adds a real abort branch where round-1 PLAN had only the LOC-overflow case.

---

## F-PLAN-06 — Byte-stability tests omit argparse `dest`

**Verdict:** AGREED, applied.

**Verification.**

`verification/tests/test_cli_parser_capabilities_regression.py:82-119` and `:137-211` confirmed: parser-tree snapshot captures command paths + long flag names, but NOT `dest`. `core/capabilities/walker.py:437-459` records `name`, `kind`, `choices`, `default`, `help`, `action`, `nargs`, `aliases` — not `dest` for optional flags.

**Action.** §2.A acceptance item 4 (parser-tree byte-stability) extended:

- Was: "Parser-tree shape (deterministic textual summary per the existing test) is byte-identical pre-split vs post-split."
- Now: "Parser-tree shape is byte-identical pre-split vs post-split (existing test). **Plus**: a new test surface `test_cli_handler_dispatch_smoke.py` exercises one non-default flag per moved handler group (≥11 smoke tests, one per handler-group module), asserting that the handler resolves correctly and produces non-error output. Catches subtle `dest` renames or handler-namespace breaks that the manifest-shape test would miss."

This is the lighter-weight option Codex named (representative CLI smoke tests vs extending the manifest schema with `dest`). 11 smoke tests is bounded; doesn't grow the manifest schema; doesn't require regenerating the snapshot.

---

## F-PLAN-07 — Snapshot regeneration "lockstep" vs "end of cycle"

**Verdict:** AGREED, applied.

**Action.** §3 + §6 reconciled:

- §3 capabilities-manifest bullet rewritten: "**Each intentional CLI-surface commit** (W-AI-2 `hai eval review`, F-PV14-02 `hai sync purge`, W-B `hai intake weight`) regenerates the manifest snapshot (`verification/tests/snapshots/cli_capabilities_v0_1_13.json`) + parser-tree snapshot (`verification/tests/snapshots/cli_help_tree_v0_1_13.txt`) **in the same commit**. The W-29 byte-stability gate asserts pre-split snapshot equality; subsequent intentional adds update the baseline atomically with the surface change."
- §6 ship-gate paragraph (was "regenerated against post-W-AI-2 + post-F-PV14-02 + post-W-B intentional adds at end of cycle") rewritten: "Regeneration happens per-W-id, not at end of cycle. Final cycle state: snapshot matches the post-W-29 + post-Phase-2/3-additions cli.py exactly."
- W-29's own acceptance items 3-5 (manifest + parser-tree + markdown byte-stability) now explicitly say "against the snapshot current at W-29 Phase 1 open" — making the comparison baseline unambiguous.

---

## F-PLAN-08 — Source docs stale (README + tactical §5D still say 9217 LOC + v0.1.16 precondition)

**Verdict:** AGREED, applied.

**Verification.**

- `reporting/plans/v0_1_17/README.md:3` says "PLAN.md authored when the cycle opens after v0.1.16 closes. v0.1.15 is already published; v0.1.16 must first absorb or defer the post-publish foreign-user findings." Confirmed stale (v0.1.16 was cancelled 2026-05-04).
- `reporting/plans/v0_1_17/README.md:13` catalogue row: "cli.py 9217-line mechanical split." Confirmed stale (current `wc -l` is 9927).
- `reporting/plans/tactical_plan_v0_1_x.md:703`: same "9217-line mechanical split" stale wording.

**Action.**

- Updated `v0_1_17/README.md` lines 3 + 13 + 24 (catalogue total) to reflect post-v0.1.16-cancellation status + current 9927 LOC. Provenance trail preserved (the original 9217 number references the v0.1.13 W-29-prep boundary table, which itself reflected the 8891 LOC pre-W-A/W-C absorbtion baseline — both citations were already-stale at v0.1.17 README author-time).
- Updated `tactical_plan_v0_1_x.md:703` row to 9927 LOC, with parenthetical "(was 9217 at the v0.1.13 W-29-prep audit; +710 LOC across v0.1.13/v0.1.14/v0.1.15/v0.1.15.1 surface adds)."
- PLAN §1.4 chain A footnote added clarifying the 9217 → 9927 drift across the multi-cycle redestination.

---

## F-PLAN-09 — W-B `agent_safe=True` contradicts user-authored-only default

**Verdict:** AGREED, applied.

**Action.** OQ-3 resolved in PLAN (not deferred to implementation-time):

- §2.H schema simplified: `source` enum reduced from `'user_authored' | 'agent_proposed' | 'wearable_pull'` → `'user_authored'` only for v1.
- §2.H acceptance item 4: `agent_safe=True` → `agent_safe=False`. `idempotent="no"` retained.
- §2.H "Subcommand shape" prose: removed `--ingest-actor` agent-blocking branch (no longer needed since `agent_safe=False` means agents respect the manifest flag and don't invoke). `--ingest-actor` flag retained as a per-record provenance field (defaults to `cli`).
- §2.H "What this WS does NOT do" gains: "Does not introduce an agent-proposal path. v1 is user-authored measurement only. A future cycle can extend the source enum + add a W57-style commit gate if agent-proposed body-comp becomes a real use case."
- OQ-3 closed in §8: "ratified per Codex round-1 F-PLAN-09 — `agent_safe=False`, user-authored-only, no `agent_proposed` enum until a commit path exists."

---

## F-PLAN-10 — AGENTS.md closure edits would drop W-29/W-30 provenance trail

**Verdict:** AGREED, applied.

**Action.** §3 governance-edit bullets rewritten with explicit provenance preservation:

- **AGENTS.md "Settled Decisions" W29/W30 entry update (at v0.1.17 ship).** "Append `**W-29 closed at v0.1.17** (mechanical split landed; manifest byte-stable; cli.py 9927 LOC → 1 main + 1 shared + 11 handler-group modules, all <2500 LOC).` to the existing entry. **Retain** the full redestination chain prose (v0.1.12 CP1/CP2 origin, v0.2.x CP-PATH-A/CP-W30-SPLIT, v0.1.14 → v0.1.15 → v0.1.17 redestination, v0.1.16 cancellation). **Retain** the W-30 destination clause (`v0.2.3 capabilities-manifest schema freeze remains scheduled`) verbatim — W-30 stays scheduled, only W-29 closes."
- **AGENTS.md "Do Not Do" cli.py-split entry update (at v0.1.17 ship).** "Current entry: `Do not split \`cli.py\` or freeze the capabilities manifest schema before their scheduled cycles (v0.1.17 / v0.2.3).` Replacement: `Do not freeze the capabilities manifest schema before its scheduled cycle (v0.2.3).` **Retain** the full origin/destination provenance tail attached to the entry (v0.1.12 CP1/CP2, post-v0.1.13 CP-W30-SPLIT, etc.). The cli.py-split clause retires; the W-30 freeze clause + its provenance stay."

The edit instructions now explicitly preserve audit chain. PLAN §3 reads as a *targeted append* to one entry and a *targeted clause-removal* in another, not a full-entry rewrite.

---

## F-PLAN-11 — D15 tier sentence misstates the threshold

**Verdict:** AGREED (close-in-place), applied.

**Action.** PLAN line 3 rewritten:

- Was: "**Tier (D15):** **substantive** — W-29 cli.py 9927-line mechanical split (1 main + 1 shared + 11 handler-group, byte-stable manifest contract) + W-B new schema (`body_comp` table + migration 026) + W-AH-2 eval substrate near-quadrupling (35 → 120+) + W-Vb-4 persona-replay residual (6 personas) ≥ 3 governance/state-model/audit-chain edits per AGENTS.md D15."
- Now: "**Tier (D15):** **substantive** — W-29 is a release-blocker workstream AND estimated effort is 25-40 days; either criterion independently satisfies AGENTS.md D15 'substantive' threshold (`≥1 release-blocker workstream` OR `≥10 days estimated`). W-B schema/state-model + W-AH-2 substrate expansion + audit-chain doc edits are scope facts, not D15 tier triggers; D15's three-edit threshold counts only governance or audit-chain edits, of which §3 has two (cli.py-split entry retirement + W-29 closure addition)."

---

## OQ disposition table

| OQ | Round-1 Codex opinion | Round-1 disposition |
|---|---|---|
| OQ-1 (`hai sync` placement) | "Acceptable; decide after refreshed boundary table" | **Held open** — re-decide at W-29 Phase 1 close, depending on `state.py` LOC headroom in the refreshed boundary note. |
| OQ-2 (W-AI-2 persistence) | "Agree with user state dir" | **Closed** — user state dir ratified. Removed from §8 open list. |
| OQ-3 (W-B W57 / agent_safe) | "Default wrong; prefer agent_safe=False, user-authored-only v1" | **Closed via F-PLAN-09 PLAN edit** — agent_safe=False, user-authored-only. Removed from §8 open list. |
| OQ-4 (W-B same-day collision) | "Agree with append" | **Closed** — append ratified. Removed from §8 open list. |
| OQ-5 (W-D projection default) | "Hold pending F-PLAN-01" | **Held open** — F-PLAN-01 fixed; OQ-5 reframed (target-anchored ratified as v1 default; linear-extrapolation reachable via threshold override). Round-2 maintainer ratification expected. |
| OQ-6 (W-AH-2 distribution) | "20/domain + 12-15 synthesis acceptable post harness fix" | **Held open** — F-PLAN-02 fixed; OQ-6 carries forward unchanged. |
| OQ-7 (W-AM-2 mechanisation) | "If staying on current `expected.policy` contract, no helper required" | **Closed via F-PLAN-02 PLAN edit** — staying on current contract. Removed from §8 open list. |
| OQ-8 (W-29 commit shape) | "Prefer 3-commit series; acceptance must be explicit" | **Held open** — added clarifying line to §2.A: "every commit in the W-29 series must individually pass acceptance items 3-10; final commit closes the byte-stability gate." Round-2 maintainer ratification expected. |

§8 open-questions list shrinks from 8 → 4 (OQ-1, OQ-5, OQ-6, OQ-8).

---

## Round 2 expectations

**Recommended next-round budget:** 1 focused round.

**Surfaces Codex should re-check:**
- Revised W-D arm-2 §2.I (target-value plumbing + corrected formula + 7 acceptance items + macro-projection scope).
- Revised W-AH-2 §2.C + W-AM-2 §2.E (existing `expected.classified` / `expected.policy` / singular `tag` contract).
- Revised W-AI-2 §2.D (split commit-gate + ship-gate acceptance).
- Revised W-29 §2.A (10 acceptance items including refreshed-boundary-note + handler-dispatch-smoke + do-not-split abort path).
- Revised §3 governance-edits + §6 snapshot-regeneration sequencing.
- Revised W-B §2.H (agent_safe=False + user-authored-only schema).
- Revised AGENTS.md §3 closure-edit instructions (provenance preservation).
- Refreshed `v0_1_17/README.md` + tactical §5D source docs.
- Tier sentence in PLAN line 3.

**Empirical settling:** AGENTS.md `10 → 5 → 3 → 0` halving signature predicts ~5-6 round-2 findings (likely second-order from round-1 revisions per AGENTS.md "Audit-chain empirical settling shape — if round N has more findings than round N-1, the previous response introduced second-order issues — re-read your own diff"). Round-2 prompt at `codex_plan_audit_round_2_prompt.md` scopes audit to revised surfaces only.

---

## Change-set summary

| File | Action |
|---|---|
| `reporting/plans/v0_1_17/PLAN.md` | 11 finding-driven revisions; §1.2/§1.3/§2.A/§2.C/§2.D/§2.E/§2.H/§2.I/§3/§4/§5/§6/§8/§9 all touched. Tier sentence rewritten. |
| `reporting/plans/v0_1_17/README.md` | Stale 9217 LOC → 9927; v0.1.16 precondition retired (lines 3 + 13 + 24). |
| `reporting/plans/tactical_plan_v0_1_x.md` | §5D row 703 LOC update. |
| `reporting/plans/v0_1_17/codex_plan_audit_response_response.md` | This file. |
| `reporting/plans/v0_1_17/codex_plan_audit_round_2_prompt.md` | Round 2 kickoff (per AGENTS.md D14 + Dom's auto-draft feedback memory). |

**Provenance.** This response-response authored 2026-05-04 against HEAD `df6a13c`. PLAN revisions land in this same edit pass; no separate commit yet (Phase 0 hasn't opened — D14 round 2 fires first).
