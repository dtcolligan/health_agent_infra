**Cycle tier (D15): substantive.**

# v0.1.14 RELEASE PROOF — Eval substrate + provenance + recovery path

**Status.** **IR chain CLOSED at round 3 (SHIP_WITH_NOTES, 1 nit applied).**
Ready for merge + PyPI publish (maintainer-handoff).
**Branch.** `cycle/v0.1.14`, 12 commits ahead of `main`.
**Date.** 2026-05-01.

## 1. Workstreams shipped

| W-id | Status | Detail |
|---|---|---|
| W-2U-GATE | **deferred → v0.1.15** | No foreign-user candidate (OQ-I) on file at pre-implementation gate; PLAN.md §1.3.1 path 2 invoked. See `pre_implementation_gate_decision.md`. |
| W-PROV-1 | **closed-this-cycle** | Source-row locator value type (`{table, pk, column, row_version}`); whitelist-validated (recovery domain v0.1.14 demo). Migration 023 adds `recommendation_log.evidence_locators_json`; `core/provenance/locator.py` (validate / dedupe / serialize / resolve / render); recovery R6 firing emits locators when `for_date_iso` + `user_id` + `accepted_state_versions` are passed; synthesis copies onto recommendation; `hai explain` renders in JSON + markdown. 21 tests. |
| W-EXPLAIN-UX | **closed-this-cycle** | P13 (low-domain-knowledge) persona added (matrix-only per F-PLAN-06); `reporting/docs/explain_ux_review_2026_05.md` filed with 8 findings, 6 v0.2.0 W52 prose obligations, and a carries-forward-to-v0.1.15-W-2U-GATE-foreign-user-pass section per §1.3.1 path 2 (maintainer-substitute reader; foreign-user empirical pass lands v0.1.15). |
| W-BACKUP | **closed-this-cycle** | `core/backup/` module + 3 new top-level CLI subcommands (`hai backup`, `hai restore`, `hai export`); versioned tarball + JSON manifest; schema-mismatch refusal with named recovery hint. `reporting/docs/recovery.md` documents 5 disaster scenarios. 8 roundtrip tests. |
| W-FRESH-EXT | **closed-this-cycle** | `test_doc_freshness_assertions.py` extends to W-id refs across summary surfaces (ROADMAP / strategic / tactical) with honest-deferral exempt-keyword set. Persona-runner pre-flight (F-PHASE0-01 absorption) calls `hai demo cleanup`; refuses on active marker. |
| W-AH | **partial-closure → v0.1.15 W-AH-2** | 28 → 35 scenarios (+7 new across recovery / running / sleep). Original 120+ target deferred to v0.1.15 W-AH-2. |
| W-AI | **partial-closure → v0.1.15 W-AI-2** | 30 judge-adversarial fixtures shipped (10 each: prompt_injection / source_conflict / bias_probe). `hai eval review` CLI deferred to v0.1.15 W-AI-2 (substrate work; not blocking v0.2.2 W58J). 7 contract tests. |
| W-AJ | **closed-this-cycle** | `core/eval/judge_harness.py` with `JudgeHarness` ABC, `NoOpJudge` reference impl, `JudgeRequest` / `JudgeResponse` dataclasses; pre-allocated `bias_panel_results` for v0.2.2 W-JUDGE-BIAS. 13 tests. |
| W-AL | **closed-this-cycle** | `core/eval/calibration_schema.py` with `AtomicClaim`, `CalibrationReport`, `validate_calibration_report`, stub `decompose_into_atomic_claims`. `reporting/docs/calibration_eval_design.md` cites FActScore (Min et al. 2023) + MedHallu (Pandit et al. 2024). |
| W-AM | **absorbed-into-W-AI + partial-closure → v0.1.15 W-AM-2** | Adversarial fixtures fold into W-AI's judge_adversarial corpus (30 fixtures, 10 per category). Explicit "should escalate" domain scenarios shipped: **2 of the originally-targeted 6**, tagged `w-am-adversarial-escalate` (recovery `rec_004_should_escalate_compound_signals.json`, running `run_004_should_escalate_acwr_max.json`). The other 4 (sleep / strength / stress / nutrition) were authored mid-cycle but failed their own expected-firing-token assertions against the live classify+policy stack and were removed; the tag-count claim is honestly **2-of-6 with 4 fork-deferred to v0.1.15 W-AM-2**. v0.1.15 W-AM-2 inherits the per-scenario interactive-author-then-validate workflow noted in REPORT.md §5.3. |
| W-AN | **closed-this-cycle** | `hai eval run --scenario-set <set>` flag added; values `domain|synthesis|judge_adversarial|all`. judge_adversarial is shape-only summary; all fan-outs domain+synthesis. |
| W-29 | **deferred → v0.1.15 W-29** | cli.py 9217-line mechanical split with byte-stable manifest preservation deemed too high-risk for single-session execution. v0.1.13 W-29-prep boundary table preserved as v0.1.15 input. |
| W-Vb-3 | **partial-closure → v0.1.15 W-Vb-4** | 3 of 9 personas closed (P2 / P3 / P6). P7..P12 fork-deferred to v0.1.15 W-Vb-4 per AGENTS.md "Honest partial-closure naming" + PLAN.md §2.M ("may further partial-close (3-at-a-time)"). Cumulative 6 of 12 (v0.1.13 closed P1+P4+P5; v0.1.14 closes P2+P3+P6). |
| W-DOMAIN-SYNC | **closed-this-cycle** | `test_domain_sync_contract.py` pins canonical six (`recovery / running / sleep / stress / strength / nutrition`) across `SUPPORTED_DOMAINS`, `PROPOSAL_SCHEMA_VERSIONS`, `DOMAIN_ACTION_ENUMS`, synthesis literal, intake/gaps literal, `_DOMAIN_TABLES` (with documented `gym↔strength` snapshot-read alias), and `_DOMAIN_ACTION_REGISTRY` (Phase-A-only exemption). 8 tests. |

**Closed-this-cycle: 8.** **Partial-closure: 3 (W-AH / W-AI / W-Vb-3).**
**Deferred: 2 (W-2U-GATE / W-29).** **Absorbed: 1 (W-AM).**

## 2. Quality gates

### 2.1 Test surface (post-IR-CLOSE round 3)

| Gate | Target | Result |
|---|---|---|
| Pytest narrow | ≥ 2540 | **2566 passed, 3 skipped, 0 failed** (+14 vs round 0's 2552 from new regression tests covering F-IR-01..07 + F-IR-R2-01..02 + F-IR-R3-01) |
| Pytest broader (-W error::Warning) | clean | **2566 passed, 3 skipped, 0 failed, 0 errors** |
| Mypy | 0 errors | **0 errors @ 127 source files** |
| Bandit -ll | 0 Med/High; ≤ 50 Low | **46 Low / 0 Medium / 0 High** |
| Ruff | clean | **All checks passed** |

### 2.5 Codex IR chain — CLOSED at round 3

| Round | Codex verdict | Findings | Maintainer disposition |
|---|---|---|---|
| 1 | SHIP_WITH_FIXES | 7 (F-IR-01..07) | 7 ACCEPT, applied + committed (`c4ac1d0`) |
| 2 | SHIP_WITH_FIXES | 2 (F-IR-R2-01, F-IR-R2-02; second-order from r1 fixes) | 2 ACCEPT, applied + committed (`2e1fe7f`) |
| 3 | SHIP_WITH_NOTES | 1 nit (F-IR-R3-01) | 1 ACCEPT, applied + close commit |

**Settling shape:** `7 → 2 → 1-nit → SHIP_WITH_NOTES`. Mirrors v0.1.12
(`5 → 2 → 0`) + v0.1.13 (`6 → 2 → 0`) at the same 3-round shape.
Round-1's higher count reflects the broader v0.1.14 surface
(security + scope-mismatch + ship-gate + provenance).
Cumulative IR findings: **10. All ACCEPT, zero DISAGREE.**

### 2.2 Capabilities byte-stability (per F-PLAN-04 expected-diff classes)

`test_cli_parser_capabilities_regression.py` snapshots regenerated for the
**named-change-accepted** W-AN + W-BACKUP + W-PROV-1 surfaces:

- W-AN added `--scenario-set` to `hai eval run`.
- W-BACKUP added `hai backup` / `hai restore` / `hai export` (3 new
  top-level subcommands; mapped under Advanced & tools per
  `core/capabilities/render.py::_CATEGORY_MAP`).
- W-PROV-1 surfaces `evidence_locators` in `hai explain` JSON +
  markdown rendering (no parser change).

Total `hai` commands: **56 → 59** (+3). `hai capabilities --markdown
> reporting/docs/agent_cli_contract.md` regenerated; the
`test_committed_contract_doc_matches_generated` test passes.

### 2.3 Audit-chain integrity

- 3-state chain (`proposal_log` → `planned_recommendation` → `daily_plan`
  + `recommendation_log` → `review_outcome`) reconciles cleanly via
  `hai explain` for fixture days 2026-04-30 / 2026-04-28 / 2026-04-27
  (Phase 0 verdict; held since).
- W-PROV-1 demo: recovery R6 firing emits + persists locators
  end-to-end (proposal → recommendation → render → resolve).

### 2.4 Persona matrix

- 13 personas (P1..P12 + new P13). P13 is matrix-only per F-PLAN-06.
- W-Vb-3 partial closure: 6 of 12 demo-replay fixtures shipped
  (P1+P4+P5 from v0.1.13 + P2+P3+P6 from v0.1.14).

## 3. Settled-decision deltas

No new D-entries this cycle. CP application status carried forward
from `pre_implementation_gate_decision.md`:

- CP-2U-GATE-FIRST — applied-but-deferred (W-2U-GATE → v0.1.15).
- CP-MCP-THREAT-FORWARD — applied-pre-cycle 2026-05-01.
- CP-DO-NOT-DO-ADDITIONS — applied-pre-cycle 2026-05-01.
- CP-PATH-A — applied-pre-cycle 2026-05-01.
- CP-W30-SPLIT — applied-pre-cycle 2026-05-01.

## 4. Audit-chain artifacts

```
reporting/plans/v0_1_14/
  PLAN.md                                                  (D14 PLAN_COHERENT closed at round 4)
  pre_implementation_gate_decision.md                      (W-2U-GATE → v0.1.15; F-PHASE0-01 → W-FRESH-EXT; OQ-J applied)
  audit_findings.md                                        (Phase 0 D11; gate fires green)
  codex_plan_audit_prompt.md + 4× round prompts/responses  (D14 chain, 12 → 7 → 3 → 1-nit → CLOSE)
  codex_implementation_review_prompt.md                    (this cycle's IR; awaiting Codex)
  RELEASE_PROOF.md                                         (this file)
  REPORT.md                                                (cycle retrospective)
```

## 5. Out of scope (named with destinations)

| Item | Destination |
|---|---|
| W-2U-GATE foreign-user empirical proof | v0.1.15 |
| W-29 cli.py mechanical split (9217 LOC) | v0.1.15 |
| W-AH-2 scenario expansion 35 → 120+ | v0.1.15 |
| W-AI-2 `hai eval review` CLI surface | v0.1.15 |
| W-AM-2 4 fork-deferred escalate-tagged scenarios (sleep / strength / stress / nutrition) | v0.1.15 |
| W-Vb-4 persona-replay residual (P7..P12) | v0.1.15 |
| W-EXPLAIN-UX foreign-user empirical pass | v0.1.15 (rides on W-2U-GATE) |
| W-FACT-ATOM FActScore atomic decomposition | v0.2.0 (folds into W58D) |
| W-MCP-THREAT artifact | v0.2.0 (per CP-MCP-THREAT-FORWARD) |
| W-COMP-LANDSCAPE / W-NOF1-METHOD docs | v0.2.0 (per OQ-E) |
| W-2U-GATE-2 (second foreign user) | v0.2.0 (sequenced after v0.1.15) |
| W52 weekly review | v0.2.0 (consumes W-PROV-1 substrate + W-AL schema) |
| W58D deterministic claim block | v0.2.0 |
| W58J LLM-judge shadow + W-JUDGE-BIAS | v0.2.2 (consumes W-AJ scaffold) |
| `hai support` redacted bundle | v0.2.0 (per OQ-M default) |
| W-30 capabilities-manifest schema freeze | v0.2.3 (per CP-W30-SPLIT) |

## 6. Ship-time freshness checklist (per AGENTS.md "Ship-time freshness")

- [ ] `ROADMAP.md` "Now" = v0.1.14 shipped; "Next" = v0.1.15.
- [ ] `AUDIT.md` v0.1.14 row added.
- [ ] `README.md` "Now/Next" reflects v0.1.14 → v0.1.15.
- [ ] `HYPOTHESES.md` cites current strategic plan.
- [ ] `reporting/plans/README.md` marks v0.1.14 as shipped.
- [ ] `reporting/plans/tactical_plan_v0_1_x.md` v0.1.15 row reflects
       fork-deferred items.
- [ ] `success_framework_v1.md` / `risks_and_open_questions.md`
       spot-check.

## 7. Provenance

Authored 2026-05-01 by Claude Opus 4.7 (1M context) at HEAD `16d2cd0`,
on branch `cycle/v0.1.14`, with:
- `uv run pytest verification/tests -q`: 2552 passed, 3 skipped, 0 fail.
- `uvx mypy src/health_agent_infra`: 0 errors.
- `uvx bandit -ll -r src/health_agent_infra`: 46 Low / 0 Med / 0 High.
- `uvx ruff check src/health_agent_infra`: clean.
- `hai capabilities --json`: 59 commands.
- `git log --oneline cycle/v0.1.14 ^main`: 8 commits.
