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

- **v0.1.13 shipped (2026-04-30).** Largest cycle in the v0.1.x track
  at 17 workstreams. Closed all v0.1.12 named-deferred items
  (W-Vb persona-replay end-to-end for P1+P4+P5 ship-set, W-N-broader
  50-site sqlite3 leak fix, W-FBC-2 multi-domain F-B-04 closure with
  per-domain carryover-uncertainty token, CP6 §6.3 strategic-plan
  edit). Shipped the originally-planned onboarding scope (`hai init
  --guided`, `hai capabilities --human`, `hai doctor --deep`,
  `hai today` cold-start prose, README rewrite + smoke test, every
  USER_INPUT exit code carries actionable next-step prose). Landed
  governance prerequisites (W-29-prep cli.py boundary audit,
  W-LINT regulated-claim lint, W-AK declarative persona
  expected-actions, W-A1C7 acceptance matrix). D14 settled at
  round 5 with the 11 → 7 → 3 → 1-nit → 0 signature; Codex IR
  closed at round 3 with 6 → 2 → 0 (cleaner than the empirical
  norm). See
  [`reporting/plans/v0_1_13/RELEASE_PROOF.md`](reporting/plans/v0_1_13/RELEASE_PROOF.md).
- **v0.1.14 in flight (next cycle).** Eval substrate + cli.py
  mechanical split + W-Vb-3 (9 non-ship-set personas residual).

## Next

- **v0.1.14 — eval substrate + cli.py split + W-Vb-3 residual.** W-29
  mechanical cli.py split (1 main + 1 shared + 11 handler-group,
  conditional on v0.1.13 W-29-prep verdict — green; the boundary
  table is in `reporting/docs/cli_boundary_table.md`), W-Vb-3
  persona-replay extension to the 9 non-ship-set personas
  (P2/P3/P6/P7/P8/P9/P10/P11/P12), L2 W-DOMAIN-SYNC scoped
  contract test, judge-adversarial fixtures (W-AI), W-AL
  calibration scaffold (schema/report shape only).
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
