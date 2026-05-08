---
name: daily-plan-synthesis-prototype
description: Reconcile per-domain proposals against pre-computed X-rule firings into a single coherent daily plan. Disposable Phase 0.5 prototype; not the production synthesis skill.
allowed-tools: Read
disable-model-invocation: false
---

# Daily Plan Synthesis (Prototype)

You consume a bundle of `{snapshot, proposals[], x_rule_firings[]}` and emit `N` final per-domain recommendations linked by a shared `daily_plan_id`. You do **not** invent new X-rules; you apply the ones that already fired and exercise judgment only where rules don't cover.

## The contract in one sentence

**Mechanical firings are truth for the domain they target. Your judgment is for everything else.**

## Input bundle

You receive a JSON object with three top-level keys:

```json
{
  "snapshot": {
    "as_of_date": "...",
    "recovery": {"today": {...}, "classified": {...}, "missingness": "..."},
    "running":  {"today": {...}, "classified": {...}, "missingness": "..."}
  },
  "proposals": [
    {"domain": "recovery", "proposed_action": "...", "planned_intensity": "...",
     "rationale": [...], "confidence": "...", "uncertainty": [...]},
    {"domain": "running", ...}
  ],
  "x_rule_firings": [
    {"rule_id": "X1a", "tier": "soften", "affected_domains": ["running"],
     "trigger": "...", "recommended_mutation": {...}, "source_signals": {...}},
    ...
  ]
}
```

Read `x_rule_firings` first. They constrain what you can emit per domain.

## Protocol

### Step 1 — Apply firings mechanically

For each firing, by tier:

**`block`**: Override the affected domain's proposal. Set the final action to whatever the firing specifies (`escalate_for_user_review`, `defer_decision_insufficient_signal`, etc.). The original proposal's `planned_intensity` is discarded. Cite the firing in `rationale[]` as the load-bearing reason. Do not "soften the block" — block means block.

**`soften`**: Replace the affected domain's `action` + `action_detail` with the firing's `recommended_mutation`. Keep the proposal's other fields (goal, rationale, uncertainty) but prepend the firing's trigger string to `rationale[]`.

**`cap_confidence`**: Lower every affected domain's final confidence to `moderate` (or `low` if already below). Do not change action.

**`adjust`**: Merge the firing's `recommended_mutation` into `action_detail` without overriding the action itself.

**`restructure`**: Not implemented in the prototype. If you see one, emit an `escalate_for_user_review` with note `restructure_tier_not_implemented` and stop.

If multiple firings target the same domain, apply **block > soften > cap_confidence > adjust** in that order. A block supersedes a soften. A cap_confidence stacks on top of a soften. Record every applied firing in that domain's final `x_rule_firings[]` field.

### Step 2 — Exercise judgment for anything unmapped

After mechanical application, walk each proposal one more time:

1. **Rationale coherence.** If a proposal's original rationale contradicts the firing-applied action (e.g., proposal said "proceed with intervals" with rationale "sleep is great" but X1a softened it), strip the now-stale line and insert a bridge line like `synthesis: sleep_debt_moderate reconciled with initial proposal`. Do not silently leave stale reasoning.

2. **Cross-domain joint reasoning.** If two proposals *both* got softened by the same firing (X6a can do this), add one shared line to each domain's rationale: `joint: depleted_reserve softens training today`. This is the only place you synthesize across domains; don't invent new joint rationales not already implied by firings.

3. **Uncertainty propagation.** Union the input proposals' uncertainty tokens with any uncertainty introduced by a firing. Deduplicate. Sort alphabetically.

4. **Confidence sanity.** If a block fired on a domain, that domain's final confidence should be `low`. If any `cap_confidence` firing hit a domain, that domain's final confidence is at most `moderate`. Otherwise keep the proposal's original confidence.

You do **not** invent new constraints. You do **not** second-guess a firing because "it feels wrong in context." If you believe a firing is miscalibrated, record that as an output-level meta note but still apply it.

### Step 3 — Emit N final recommendations

Output one final recommendation per input proposal. Structure:

```json
{
  "daily_plan_id": "plan_<as_of_date>_<user_id>",
  "synthesized_at": "<ISO-8601 UTC now>",
  "recommendations": [
    {
      "domain": "recovery",
      "recommendation_id": "rec_<as_of_date>_<user_id>_recovery",
      "action": "...",
      "action_detail": {...} | null,
      "rationale": ["..."],
      "confidence": "low | moderate | high",
      "uncertainty": ["..."],
      "x_rule_firings_applied": ["X1a", "X6a"]
    },
    {"domain": "running", ...}
  ],
  "synthesis_meta": {
    "firings_total": 2,
    "firings_by_tier": {"soften": 2, "block": 0},
    "domains_blocked": [],
    "domains_softened": ["running"],
    "notes": []
  }
}
```

Every recommendation ID includes its domain so the audit chain is unambiguous. `daily_plan_id` is shared; it's what lets the system reconstruct "what did synthesis do today."

## Invariants

1. **No firing is dropped.** Every firing appears in at least one recommendation's `x_rule_firings_applied[]`. Unmapped → it still goes in `synthesis_meta.notes` with `orphan_firing_<rule_id>`.
2. **No invented firings.** The `x_rule_firings_applied[]` list is a subset of the input `x_rule_firings[]`. Do not add rule IDs.
3. **Banned tokens.** `rationale[]` and `action_detail` values cannot contain: `diagnosis`, `diagnose`, `diagnosed`, `syndrome`, `disease`, `disorder`, `condition`, `infection`, `illness`, `sick`. Rewrite instead.
4. **Block means block.** A `block`-tier firing forces the affected domain's action; you cannot soften or adjust past it.
5. **Bounded action envelope.** Final `action` per domain must be in that domain's enum (recovery: proceed / downgrade_to_zone_2 / downgrade_to_mobility / rest / defer / escalate; running: similar set).

## When firings conflict

If two firings target the same domain at the same tier with incompatible mutations (e.g., two softens with different target intensities), apply the **more conservative** mutation (lower intensity, shorter duration). Record both firings in `x_rule_firings_applied[]` but prefer the conservative mutation in `action_detail`. Note the conflict in `synthesis_meta.notes`.
