---
name: daily-plan-synthesis
description: Reconcile per-domain proposals into a coherent daily plan by composing rationale and uncertainty across domains. The runtime already applied every Phase A X-rule mutation mechanically; this skill adds the human-legible joint narration on top. It never computes bands, evaluates R-rules, or applies X-rule mutations — those are runtime-owned.
allowed-tools: Read, Bash(hai state snapshot *), Bash(hai synthesize *)
disable-model-invocation: false
---

# Daily Plan Synthesis

Your job: given the snapshot, the per-domain proposals, and the list of Phase A X-rule firings the runtime already applied, write the prose layer that ties the day's recommendations together. Rationale per domain, uncertainty per domain, joint narration when domains interact.

You do not pick actions. You do not re-evaluate X-rules. You do not change confidence. The runtime has already done all of that.

## Load the bundle

```
hai synthesize --as-of <today> --user-id <u> --bundle-only
```

`--bundle-only` is read-only: it emits the bundle as JSON on stdout and does not commit. The orchestration layer uses your `--drafts-json` overlay in a second call to finish the commit.

The bundle is three blocks:

- `snapshot` — today's full cross-domain snapshot (`recovery`, `running`, `stress`, `nutrition`, `notes`, `goals`, `missingness`). Same shape as `hai state snapshot` plus the per-domain `classified_state` + `policy_result` when available.
- `proposals` — list of `DomainProposal` dicts already in `proposal_log` for `(for_date, user_id)`.
- `phase_a_firings` — list of `XRuleFiring` dicts the runtime will apply (or has already applied) to produce mechanical drafts. Rule ids like `X1a`, `X3b`, `X6a`, `X7`. `recommended_mutation` holds the mutation; `source_signals` holds the triggering snapshot values.

Phase B firings (`X9` today, more later) are NOT in your bundle. Those run AFTER you return — you will never see them, and you must not try to emit them.

## Protocol

### 1. Read the mechanically-mutated draft for each domain

Each proposal in `proposals` has a mirror draft the runtime built by applying relevant Phase A mutations. For a given proposal, read the firings whose `affected_domain` matches to understand what the runtime changed:

- `tier=soften` + `recommended_mutation.action=<downgrade>` → the draft's `action` is that downgrade.
- `tier=block` + `recommended_mutation.action=escalate_for_user_review` → the draft's `action` is escalate. Block tier wins over soften when both fire.
- `tier=cap_confidence` → the draft's `confidence` is `moderate` (never raised, only lowered from `high`).

You edit the draft. But only:
- `rationale` — rewrite as a list of strings, one line per band or firing you want to surface.
- `uncertainty` — add tokens for missingness, vendor disagreements, coverage caveats.
- `follow_up.review_question` — optionally tailor the question to the final action.

You do NOT touch `action`, `action_detail`, `confidence`, `recommendation_id`, `daily_plan_id`, `for_date`, or `user_id`. The runtime silently ignores any of those edits — they are runtime-owned after Phase A.

### 2. Compose the rationale

One line per reason. Reasons come from three places:

1. **The proposal's own `rationale`** — the classified state that drove the domain's pick. Example: `weekly_mileage_trend=high`, `sleep_debt=moderate`.
2. **The X-rule firings** — name the rule id and its trigger. Example: `x1a_sleep_debt_moderate_cap`, `x3b_acwr_spike=1.52`.
3. **Cross-domain joint reasons** — only when multiple domains' firings share the same source signal. Example: if recovery and running both softened on `body_battery=22`, surface `body_battery_end_of_day=22` ONCE on whichever domain's draft is the primary for the day, and reference it as context on the other.

Do not duplicate firings across drafts. Do not invent rationale tokens that don't trace to a firing or a band.

### 3. Compose the uncertainty

Start with the proposal's `uncertainty`. Append tokens for:

- Missingness: look at `snapshot.missingness.<domain>`. If the domain's coverage is partial or an expected signal is `unavailable_at_source`, add a matching uncertainty token.
- Vendor disagreement: propagate any `agent_vendor_*_disagreement` already on the proposal.
- Cross-domain cap: if X7 fired, add `stress_capped_confidence`. If X6 fired, add `body_battery_softened`.

Sort alphabetically; deduplicate.

### 4. Tailor `follow_up.review_question` if the action changed

If the draft's `action` differs from the proposal's (X-rule mutated it), adjust the review question to match the final action. Example: running proposal was `proceed_with_planned_run` but `X1a` softened to `downgrade_to_easy_aerobic` — the review question should ask about the easy run outcome, not the planned hard run.

Otherwise keep the runtime-supplied default.

### 5. Return drafts

Emit a JSON array of partial recommendation dicts, keyed by `recommendation_id`, carrying only your overlay fields:

```json
[
  {
    "recommendation_id": "rec_2026-04-17_u_local_1_running_01",
    "rationale": ["weekly_mileage_trend=high", "x1a_sleep_debt_moderate_soften"],
    "uncertainty": ["sleep_capped_confidence", "stress_capped_confidence"],
    "follow_up": {"review_question": "Did the easy aerobic run leave you feeling fresher today?"}
  }
]
```

Save to a file and call:

```
hai synthesize --as-of <date> --user-id <u> --drafts-json <path>
```

The CLI overlays your edits onto the mechanical drafts, runs Phase B, validates each final recommendation, and commits the whole plan atomically.

## Invariants

- You never compute a band, a score, or an X-rule trigger. The runtime did those already and the firings list is the source of truth for what fired.
- You never apply an X-rule mutation. The runtime applied Phase A mutations mechanically before you saw the drafts; you see the results, not the mutations.
- You never see Phase B firings. Phase B (`X9`) runs after you return. If you catch yourself reasoning about `X9`, stop — your drafts must not depend on it.
- You never change `action`, `action_detail`, `confidence`, or `daily_plan_id`. Those are runtime-owned.
- You never emit an X-rule firing yourself. Firings come from `core/synthesis_policy.py`; skills never add to the firings list.
- If a rationale line isn't traceable to a proposal band or a Phase A firing, delete it.
- If a decision isn't reasoned in the final `rationale[]`, it didn't happen — and the operator will see the rationale, not your prose buffer.
- v0.1.7: although `allowed-tools` grants `Bash(hai synthesize *)` (broadened in v0.1.7 W25 to avoid order-sensitive permission matching against constrained patterns), this skill MUST only invoke `hai synthesize --bundle-only` (read-only) and `hai synthesize --drafts-json <path>` (overlay commit). It MUST NOT invoke `hai synthesize --supersede` or any other write form — those are operator/agent-host concerns, not skill concerns.
