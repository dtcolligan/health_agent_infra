# Explainability — `hai explain`

The runtime already persists everything needed to reconstruct why a
plan exists. `hai explain` is the read-only CLI that pulls that audit
chain back together for a human operator or an inspecting agent. It is
the supported surface the [`query_taxonomy.md`](query_taxonomy.md) §2.3
"Explanation / audit" class points at.

This doc pairs with [`memory_model.md`](memory_model.md) (where each
audit row lives on disk) and
[`personal_health_agent_positioning.md`](personal_health_agent_positioning.md)
(why the audit chain is the project's strongest differentiator).

## 1. What it is, in one paragraph

`hai explain` reconstructs a single committed plan from local SQLite —
the proposals that fed synthesis, the aggregate **planned** plan
(the pre-X-rule bundle, from the migration-011
`planned_recommendation` ledger), the X-rule firings that mutated
drafts, the final **adapted** recommendations that were committed,
the supersession linkage if any, and the review records if any have
been captured. It opens no write transaction, recomputes nothing, and
fabricates nothing: a field that the runtime never wrote comes back
empty, not invented.

The surface is the **three-state audit chain** — planned → adapted →
performed — rendered side-by-side so an agent asked *"why did you
tone down my run?"* can answer from persisted rows alone: the
planned action, the adapted action, the triggering firing, and the
firing's one-sentence `human_explanation` (which the agent narrates
verbatim).

## 2. CLI surface

```
hai explain --for-date <YYYY-MM-DD> --user-id <u>     [--text] [--db-path <p>]
hai explain --daily-plan-id <id>                       [--text] [--db-path <p>]
```

- The two selector forms are mutually exclusive. Use `--for-date` /
  `--user-id` for the canonical plan; use `--daily-plan-id` for an
  exact id (including `_v<N>` supersession variants).
- Default output is JSON, suitable for programmatic consumers.
- `--text` emits an operator-facing report grouped by audit layer.
- `--db-path` falls through to the canonical default (`$HAI_STATE_DB`
  or `~/.local/share/health_agent_infra/state.db`).

Failure modes the surface exits `2` for:

- DB not initialized at the resolved path.
- Selector form missing or both forms combined.
- Plan id (or canonical id derived from date/user) not found.

## 3. Bundle shape

The JSON bundle is a single object with seven stable top-level keys:
`plan`, `proposals`, `planned_recommendations`, `x_rule_firings`,
`recommendations`, `reviews`, `user_memory`. Field names mirror the
dataclass attributes in
`src/health_agent_infra/core/explain/queries.py`.

The pairing `proposals` ↔ `planned_recommendations` ↔
`recommendations` is the three-state view: per-domain planned intent,
aggregate pre-X-rule plan, and aggregate adapted plan. Legacy plans
committed before migration 011 land with `planned_recommendations:
[]` and degrade cleanly to the two-state view (adapted + performed).

```json
{
  "plan": {
    "daily_plan_id": "...",
    "user_id": "...",
    "for_date": "YYYY-MM-DD",
    "synthesized_at": "ISO-8601",
    "agent_version": "claude_agent_v1",
    "supersedes": "<plan_id>" | null,
    "superseded_by": "<plan_id>" | null,
    "x_rules_fired": ["X1a", "X7", ...],
    "synthesis_meta": { ... }
  },
  "proposals": [
    {
      "proposal_id": "...",
      "domain": "recovery|running|sleep|stress|strength|nutrition",
      "schema_version": "<domain>_proposal.v1",
      "action": "...",
      "action_detail": ... | null,
      "confidence": "low|moderate|high",
      "rationale": ["..."],
      "uncertainty": ["..."],
      "policy_decisions": [{"rule_id": "...", "decision": "...", "note": "..."}],
      "produced_at": "ISO-8601" | null,
      "validated_at": "ISO-8601" | null
    }
  ],
  "planned_recommendations": [
    {
      "planned_id": "planned_<for_date>_<user_id>_<domain>_01",
      "proposal_id": "<FK back to proposal_log>",
      "domain": "recovery|running|sleep|stress|strength|nutrition",
      "action": "<pre-X-rule action>",
      "action_detail": { ... } | null,
      "confidence": "low|moderate|high",
      "schema_version": "planned_recommendation.v1",
      "captured_at": "ISO-8601"
    }
  ],
  "x_rule_firings": {
    "phase_a": [
      {
        "firing_id": 1,
        "rule_id": "X1a",
        "public_name": "sleep-debt-softens-hard",
        "human_explanation": "Sleep debt is moderate, so hard sessions are softened to reduce injury risk while sleep recovers.",
        "tier": "soften|block|cap_confidence|restructure",
        "affected_domain": "...",
        "trigger_note": "...",
        "mutation": { ... } | null,
        "source_signals": { ... },
        "orphan": false,
        "fired_at": "ISO-8601"
      }
    ],
    "phase_b": [
      {
        "firing_id": 2,
        "rule_id": "X9",
        "public_name": "training-intensity-bumps-protein",
        "human_explanation": "Training is hard today, so the nutrition target bumps protein to support adaptation.",
        "tier": "adjust",
        "...": "..."
      }
    ]
  },
  "recommendations": [
    {
      "recommendation_id": "...",
      "domain": "...",
      "schema_version": "<domain>_recommendation.v1",
      "action": "...",
      "action_detail": ... | null,
      "confidence": "...",
      "bounded": true,
      "rationale": ["..."],
      "uncertainty": ["..."],
      "policy_decisions": [...],
      "issued_at": "ISO-8601",
      "review_event_id": "..." | null,
      "review_question": "..." | null,
      "supersedes": "<recommendation_id>" | null,
      "superseded_by": "<recommendation_id>" | null
    }
  ],
  "reviews": [
    {
      "review_event_id": "...",
      "recommendation_id": "...",
      "domain": "...",
      "review_at": "ISO-8601",
      "review_question": "...",
      "outcomes": [
        {
          "outcome_id": 1,
          "recorded_at": "ISO-8601",
          "followed_recommendation": true,
          "self_reported_improvement": true | false | null,
          "free_text": "..." | null
        }
      ]
    }
  ],
  "user_memory": {
    "as_of": "YYYY-MM-DDTHH:MM:SS+00:00",
    "counts": {
      "goal": <int>, "preference": <int>,
      "constraint": <int>, "context": <int>,
      "total": <int>
    },
    "entries": [
      {
        "memory_id": "...",
        "user_id": "...",
        "category": "goal|preference|constraint|context",
        "key": "..." | null,
        "value": "...",
        "domain": "recovery|running|sleep|stress|strength|nutrition" | null,
        "created_at": "ISO-8601",
        "archived_at": "ISO-8601" | null,
        "source": "user_manual",
        "ingest_actor": "hai_cli_direct|claude_agent_v1"
      }
    ]
  }
}
```

### Phase A vs Phase B

Today's runtime evaluates Phase A rules over `(snapshot, proposals)`
and Phase B rules over the post-overlay `final_recommendations`
(`architecture.md` §"Data flow"). Persisted firings carry no `phase`
column directly; the renderer infers Phase B from `tier == "adjust"`
(only X9 uses it). Anything else lands in `phase_a`. If a future rule
introduces a new Phase B tier, the classification rule lives in
`src/health_agent_infra/core/explain/queries.py` (`_PHASE_B_TIERS`).

### Supersession linkage

The bundle reports two pointers per plan:

- `superseded_by` — read directly from the plan's
  `synthesis_meta_json.superseded_by`. Set by `hai synthesize
  --supersede` on the prior canonical when a fresh `_v<N>` is written.
- `supersedes` — derived by looking up the plan whose
  `synthesis_meta_json.superseded_by` equals this plan's id. Lets a
  variant report the canonical it replaced.

Both pointers are `null` for an unreplaced canonical plan. To walk a
chain, follow the pointers and reissue `hai explain --daily-plan-id`
for each step.

## 4. Source tables

| Bundle field | Source table | Selector |
|---|---|---|
| `plan` | `daily_plan` | `daily_plan_id` |
| `proposals` | `proposal_log` | `WHERE daily_plan_id = ?` |
| `x_rule_firings.phase_a` / `.phase_b` | `x_rule_firing` | `WHERE daily_plan_id = ?`, split by tier |
| `recommendations` | `recommendation_log` | `WHERE json_extract(payload_json, '$.daily_plan_id') = ?` |
| `reviews[].review_*` | `review_event` | `WHERE recommendation_id IN (...)` |
| `reviews[].outcomes[]` | `review_outcome` | `WHERE review_event_id IN (...)` |
| `user_memory.entries[]` | `user_memory` | `WHERE user_id = ? AND created_at <= <for_date_eod> AND (archived_at IS NULL OR archived_at > <for_date_eod>)` |

The recommendation lookup uses `json_extract` because
`recommendation_log` carries `daily_plan_id` inside `payload_json`
rather than as a column — the same pattern
`delete_canonical_plan_cascade` uses on the write side
(`core/state/projector.py`). When migration 003 originally added the
synthesis layer it did not add a FK column on `recommendation_log`;
that decision is still load-bearing for the read path.

## 5. What `hai explain` deliberately does not do

- **Mutate state.** No `INSERT`, no `UPDATE`, no `DELETE`. The Phase C
  acceptance criteria pin this and the test suite asserts row counts
  before/after a JSON or text run are identical.
- **Recompute classification, policy, or X-rules.** A user wanting to
  see what the runtime *would* do today should use
  `hai state snapshot` and `hai synthesize --bundle-only`, not
  `hai explain`. The explain surface only shows what the runtime
  already wrote.
- **Fabricate missing rationale.** If the synthesis transaction wrote
  a proposal with no `uncertainty` lines, the bundle reports an empty
  list. If a recommendation was never reviewed, `reviews` is empty for
  it. Honesty depends on the runtime having written what it did.
- **Aggregate across days or users.** Each call returns one plan. A
  longitudinal view belongs to `hai review summary` and direct reads
  of `accepted_*_state_daily` (see
  [`query_taxonomy.md`](query_taxonomy.md) §2.4), not here.
- **Recompute** active user memory. The `user_memory` bundle (Phase D)
  is surfaced under the new top-level `user_memory` key alongside the
  plan / proposals / firings / recommendations / reviews layers — see
  `memory_model.md` §2.1 for the table shape and time-axis semantics.
  The bundle carries entries that were active at the plan's `for_date`,
  but explain itself runs no mutations on the memory layer: it only
  reads and shapes it.

## 6. Use cases

### Operator: "Why did the runtime soften my run today?"

```sh
hai explain --for-date 2026-04-17 --user-id u_local_1 --text
```

Read `## Phase A X-rule firings` for the rule that fired (e.g. `X1a
(soften) → running`), then `## Final recommendations` for the
committed action, and `## Reviews` for any captured outcome.

### Agent: "Reconstruct yesterday's plan to inform today's narration"

```sh
hai explain --for-date 2026-04-16 --user-id u_local_1
```

The JSON bundle is structured for direct ingestion. The agent can map
`x_rule_firings.phase_a` to find what mutated each draft, then read
`recommendations[].rationale` for the rationale the prior run already
wrote.

### Investigator: "Walk a supersession chain"

```sh
hai explain --daily-plan-id plan_2026-04-17_u_local_1
# → plan.superseded_by = plan_2026-04-17_u_local_1_v2
hai explain --daily-plan-id plan_2026-04-17_u_local_1_v2
# → plan.supersedes = plan_2026-04-17_u_local_1
```

## 7. Where it lives in the code

- `src/health_agent_infra/core/explain/queries.py` — read-only
  loaders, dataclasses, and the supersession lookup.
- `src/health_agent_infra/core/explain/render.py` — JSON shape and
  human-readable renderer.
- `src/health_agent_infra/cli.py` — `hai explain` subcommand wiring.
- `safety/tests/test_cli_explain.py` — end-to-end CLI tests covering
  six-domain reconstruction, plan-id vs date/user equivalence, text
  output, supersession linkage, and read-only invariants.
