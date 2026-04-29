# Roadmap

Now, next, and later. **The release-by-release plan of record lives in
[`reporting/plans/tactical_plan_v0_1_x.md`](reporting/plans/tactical_plan_v0_1_x.md)**
(next 6-8 releases) and the longer-horizon strategy in
[`reporting/plans/strategic_plan_v1.md`](reporting/plans/strategic_plan_v1.md).
The earlier
[`reporting/plans/historical/multi_release_roadmap.md`](reporting/plans/historical/multi_release_roadmap.md)
is superseded as of 2026-04-27.

This file is a high-level pointer; for actual scope, read those plans.

## Now

- **v0.1.11 shipped (2026-04-28).** Audit-cycle deferred items closed;
  persona matrix expanded 8 → 12; property-based testing for the policy
  DSL; demo isolation contract shipped (boundary-stop replay). Closed four
  D14 plan-audit rounds + four implementation-review rounds. See
  [`reporting/plans/v0_1_11/RELEASE_PROOF.md`](reporting/plans/v0_1_11/RELEASE_PROOF.md).
- **v0.1.12 in flight.** Carry-over closure + trust repair.
  **Closed:** mypy stylistic class (W-H2, 22 → 0), D13 consumer-
  site symmetry (W-D13-SYM), privacy doc + `hai auth remove`
  (W-PRIV), `strength_status` enum surface (W-FCC), public-doc
  freshness sweep (W-AC), carry-over register (W-CARRY), six
  cycle proposals (W-CP).
  **Partial closure:** demo packaged-fixture path + skeleton
  loader (W-Vb; persona-replay end-to-end deferred to v0.1.13
  W-Vb), supersede-policy design + `--re-propose-all` flag
  (W-FBC; recovery prototype + multi-domain enforcement deferred
  to v0.1.13 W-FBC-2).
  **Fork-deferred:** `-W error::Warning` broader gate (W-N-broader;
  49 + 1 sqlite3 leak sites deferred to v0.1.13 W-N-broader; v0.1.12
  ships v0.1.11 narrow gate unchanged).
  See [`reporting/plans/v0_1_12/PLAN.md`](reporting/plans/v0_1_12/PLAN.md).

## Next

- **v0.1.13 — onboarding + cli.py-split prep + carried v0.1.12 residuals.**
  Trusted-first-value gate + acceptance-matrix (5 paths × required result),
  declarative persona expected-actions (W-AK), regulated-claim lint (W-LINT),
  W-29-prep cli.py boundary audit (per CP1), W-FBC-2 (recovery prototype +
  multi-domain F-B-04 closure, inherited from v0.1.12 partial), W-Vb
  persona-replay end-to-end (proposal pre-population + clean-wheel synthesis
  test, inherited from v0.1.12 partial), W-N-broader broader-warning gate
  (49 + 1 sqlite3 leak sites, fork-inherited from v0.1.12).
- **v0.1.14 — eval substrate + cli.py split.** W-29 mechanical cli.py
  split (1 main + 1 shared + 11 handler-group, conditional on v0.1.13
  prep verdict), L2 W-DOMAIN-SYNC scoped contract test, judge-adversarial
  fixtures (W-AI), W-AL calibration scaffold (schema/report shape only).
- **v0.2.0 — weekly review + insight ledger + factuality gate.** W52
  weekly review with source-row locators, W53 insight ledger, W58
  deterministic claim-block (blocking from day 1), W58 LLM judge ships
  shadow-by-default with `HAI_W58_JUDGE_MODE` flag (flip to blocking
  within v0.2.0 or v0.2.0.x once shadow evidence supports). W-30
  capabilities-manifest schema freeze as last act of cycle (per CP2).
- **v0.3+ — MCP staging.** v0.3 plans MCP server (read-surface design +
  threat-model artifact + provenance import contract). v0.4 prereqs
  land (least-privilege scope model + threat-model completion). v0.4-or-
  v0.5 ships MCP read surface. **No write surface ever.** Per CP4.
- **v0.5+ — calibration substrate.** Read-only UI decision-checkpoint
  (per existing strategic plan).

## Later

- **v0.6 — personal-evidence estimator.** Reads 90+ days of v0.5 triples
  and produces per-user effect estimates with explicit uncertainty.
- **v0.7 — governed adaptation.** LLM proposes structured threshold
  mutations citing estimator output; user approves or rejects.
- **v1.0 — stable contract.** Acceptance requires at least three months of
  zero-incident operation after v0.7.

## Explicitly Out Of Scope

- Hosted multi-user product.
- Web/mobile/dashboard frontend.
- Meal-level nutrition, food taxonomy, or micronutrient inference in v1.
- Clinical claims or diagnosis-shaped language.
- Hidden learning loop or automatic threshold mutation from outcomes.

Full non-goals are in
[`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).

## Dependency Chain

```text
v0.1.9 weekly review
    -> v0.2 artifacts/BCTO
    -> v0.3 extension contracts + data-quality drift + first-run UX
    -> v0.4 MCP/provenance
    -> v0.5 N-of-1 substrate
         -> 90+ days of accumulated triples
         -> v0.6 estimator
             -> v0.7 governed adaptation
                 -> 3+ months zero-incident
                 -> v1.0 stable contract
```

The five bets behind this sequence are in [HYPOTHESES.md](HYPOTHESES.md).
If a falsification signal fires, the affected release gets re-scoped before
it ships.
