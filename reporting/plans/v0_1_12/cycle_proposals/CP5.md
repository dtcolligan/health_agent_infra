# CP5 — Adopt v0.2.0 substantial-with-shadow shape (D1)

**Cycle:** v0.1.12.
**Author:** Claude (delegated by maintainer).
**Codex round-4 verdict:** `accept`.
**Application timing:** at v0.1.12 ship — reshapes strategic
plan §7 Wave 2 + tactical plan §6 v0.2.0.

---

## Rationale

Maintainer adjudication 2026-04-29 (chat):

- *"I would like v0.2.0 to be pretty substantial, we can always
  fix bugs in future is they appear."*
- On the LLM judge specifically: *"You're right, we should be
  more cautious on the LLM judge in blocking mode."*

The reconciliation §3 D1 disagreement was between Codex's
3-release split (v0.2.0 deterministic only / v0.2.1 W53 + judge
shadow / v0.2.2 judge blocking) and Claude's atomic v0.2.0
(W52 + W53 + W58 all in one). Maintainer override toward "more
substantial" + "more cautious on LLM judge specifically"
collapses staging into a single release with the LLM judge
mode controlled by a feature flag.

**Synthesis:** v0.2.0 ships substantially — W52 weekly review +
W53 insight ledger + W58 factuality gate — but the W58 layer has
two parts:

1. **Deterministic claim-block** — every quoted quantitative
   claim must be source-row-locator-grounded. Blocking from day
   1.
2. **LLM judge** — residual judgment on causal framing, missing
   uncertainty, overconfident tone. Ships **shadow-by-default**
   with `HAI_W58_JUDGE_MODE = shadow | blocking` env flag. Flip
   to blocking happens within v0.2.0 (or a v0.2.0.x patch) once
   shadow-mode evidence supports it.

Memory-poisoning fixtures land alongside the shadow-mode judge —
the prior plan deferred them; CP5 brings them in.

## Current strategic plan text (verbatim, verified on disk 2026-04-29)

**`strategic_plan_v1.md:436-442` — Wave 2 row:**

```
### Wave 2 — Weekly review + insight ledger (v0.2, ~4-8 weeks post Wave 1)

**Theme.** Make the runtime useful beyond one day. W52 weekly
review + W53 insight proposal ledger. Was scoped as v0.1.9 in the
2026-04-25 roadmap; v0.1.9 cut to hardening only, so it slips here.

**Evidence anchor:** Roadmap §4 v0.1.9 (entire scope migrates).
```

**`tactical_plan_v0_1_x.md:364-405` — §6 v0.2.0 section** (full
in-scope + acceptance + effort + context). Key line at `:380-382`:

```
- **W58: LLM-judge factuality gate for weekly review** with
  agent-judge negotiation loop. Local Prometheus-2-7B (or
  comparable) pinned by SHA. Builds on v0.1.14's harness.
```

And `:390-392`:

```
- Factuality judge runs on every weekly review, blocks delivery
  when ≥ 1 unsupported quantitative claim is found, judge model
  SHA + score logged with the review.
```

(Currently asserts blocking behavior from day 1 — CP5 reframes.)

## Proposed delta — strategic plan + tactical plan

**Strategic plan `:436-442` Wave 2 — extend "Theme" line:**

```
**Theme.** Make the runtime useful beyond one day. W52 weekly
review + W53 insight proposal ledger + W58 factuality gate (deterministic
claim-block from day 1; LLM-judge layer ships shadow-by-default with
feature-flag flip to blocking once shadow-mode evidence supports it).
Was scoped as v0.1.9 in the 2026-04-25 roadmap; v0.1.9 cut to
hardening only, so it slips here.
```

**Tactical plan §6.1 — replace W58 line + add deterministic-block
W-id (e.g. W58D):**

```
- **W52: `hai review weekly --week YYYY-Www [--json|--markdown]`.**
  Code-owned aggregation across accepted state, intent, target,
  recommendation, X-rule firing, review outcome, data quality.
  **Source-row locators required for every quantitative claim**
  (carrier: `recommendation_evidence_card.v1` schema per CP-bound
  C8).
- **W53: Insight proposal ledger** (`insight_proposal` + `insight`
  tables).
- **W58D: Deterministic factuality gate.** Every quoted
  quantitative claim in weekly-review prose must resolve to a
  source-row locator. Blocking from day 1. No LLM in this layer.
- **W58J: LLM judge layer.** Residual judgment on causal framing,
  missing uncertainty, overconfident tone. Ships shadow-by-default
  with `HAI_W58_JUDGE_MODE = shadow | blocking` env flag. Logs
  every shadow-mode judgement to `judge_decision_log` table for
  evidence accumulation. Flag flip to blocking happens within
  v0.2.0 (or v0.2.0.x patch) once shadow-mode evidence shows ≤ 5%
  false-block rate over ≥ 50 weekly reviews. Memory-poisoning
  fixtures land alongside shadow mode.
```

**Tactical plan §6.2 acceptance — replace blocking line:**

```
- Factuality judge: deterministic claim-block enforces from day
  1 (W58D). LLM judge (W58J) ships shadow-by-default; logs every
  decision; flag-flip threshold + procedure documented in PLAN.
  Memory-poisoning fixtures present.
```

## Affected files

- `reporting/plans/strategic_plan_v1.md` — Wave 2 theme line
  extended.
- `reporting/plans/tactical_plan_v0_1_x.md` — §6.1 + §6.2
  rewritten per delta above.
- `reporting/plans/v0_1_12/PLAN.md` §1.3 — already updated to
  reflect the single-substantial v0.2.0 shape (round-1 fix).
- v0.2.0 PLAN.md (when authored) — implements the W52 + W53 +
  W58D + W58J split with the env-flag mechanism.

## Dependent cycles

- **v0.1.13 onwards** — onboarding cycle adds W-LINT regulated-
  claim lint that lands before W52 prose generation. Persona
  expected-actions become declarative (W-AK) — both Wave 2
  preconditions.
- **v0.1.14** — eval substrate including A12 judge-adversarial
  fixtures fold into W-AI; calibration scaffold (A2/W-AL).
- **v0.2.0** — the cycle this CP shapes. Single substantial
  release.
- **v0.2.0.x or v0.2.1** — feature-flag flip from shadow to
  blocking once evidence accumulates.

## Acceptance gate

- `accepted`: strategic + tactical plans reshaped at v0.1.12
  ship per delta above. PLAN.md §1.3 deferral row already
  reflects single-v0.2.0 shape.
- `accepted-with-revisions`: revised shape applied. Maintainer
  judgement on the ≤ 5% false-block-rate threshold + ≥ 50
  weekly reviews evidence bar is open for revision; the
  shadow-by-default + flag mechanism is non-negotiable.
- `rejected`: strategic + tactical plans unchanged. v0.2.0 PLAN
  re-scopes when authored. PLAN.md §1.3 reverts to 3-release
  split shape (v0.2.0 deterministic / v0.2.1 shadow / v0.2.2
  blocking).

## Round-4 codex verdict

`accept`. Codex round-4 confirmed the single-substantial v0.2.0
shape with shadow-by-default flag is internally coherent and
matches maintainer adjudication.
