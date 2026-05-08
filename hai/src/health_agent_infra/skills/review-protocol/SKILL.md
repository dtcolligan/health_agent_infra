---
name: review-protocol
description: Schedule, record, and summarise review outcomes against previously-issued recommendations via `hai review`. Use when yesterday's plan needs a review question scheduled, when the user reports whether a recommendation helped, or when you need a history summary before reasoning about future confidence.
allowed-tools: Bash(hai review *), Read, Write
disable-model-invocation: false
---

# Review Protocol

You don't persist anything yourself. The `hai` CLI owns all local state mutation. Your job is to call the right subcommand with validated input.

## Scope

This skill covers the three `hai review` subcommands. It is the **only** skill that writes review events and outcomes — every per-domain skill defers to this one via the follow-up section of its recommendation.

Recommendations themselves are persisted by `hai synthesize` (the atomic daily-plan commit). This skill does not write recommendations.

## Review scheduling

After a synthesis produces a per-domain recommendation with a `follow_up.review_event_id`, schedule the question:

```bash
hai review schedule --recommendation-json /path/to/recommendation.json \
                    --base-dir <base_dir> \
                    --db-path <state.db>
```

Appends to `review_events.jsonl` and projects into `review_event`. Idempotent on `review_event_id`.

`<base_dir>` is any directory you control; the CLI creates it on first use. Convention in this repo: sibling of the state DB, e.g. `~/.local/share/health_agent_infra/writeback/`.

## Review outcome recording

When the user reports whether a recommendation helped, construct a `ReviewOutcome` JSON and call:

```bash
hai review record --outcome-json /path/to/outcome.json \
                  --base-dir <base_dir> \
                  --db-path <state.db>
```

Minimum payload shape:

```json
{
  "review_event_id": "rev_2026-04-18_user_recovery",
  "recommendation_id": "rec_2026-04-17_user_recovery_01",
  "user_id": "user",
  "domain": "recovery",
  "followed_recommendation": true,
  "self_reported_improvement": true,
  "free_text": "felt good, hit all intervals"
}
```

The M4 enrichment fields (`completed`, `intensity_delta`, `duration_minutes`, `pre_energy_score`, `post_energy_score`, `disagreed_firing_ids`) are all optional; land NULL when omitted. They can be passed inline in the JSON or via the matching CLI flags, which override the JSON.

**Re-link on supersede (D1).** If the target recommendation's plan was superseded (because the user re-authored the day via `hai synthesize --supersede`), the CLI automatically re-links the outcome to the canonical leaf's matching-domain rec. Stderr gets a `re-linked from … to …` note; stdout JSON shows the effective (re-linked) recommendation id. If the leaf has no matching-domain rec, the CLI refuses with exit code `USER_INPUT` rather than create an orphan.

Outcomes are **append-only**; don't call twice for the same event unless deliberately.

## Summarising review history

For the reporting skill or for your own context before producing new recommendations:

```bash
hai review summary --base-dir <base_dir> \
                   [--user-id <id>] \
                   [--domain recovery|running|sleep|strength|stress|nutrition]
```

Emits counts by outcome category (`total`, `followed_improved`, `followed_no_change`, `followed_unknown`, `not_followed`) plus an `enriched` aggregate block when any M4 field was recorded. This is bookkeeping — no classifier inference.

## Invariants

- All state mutation goes through `hai`. Never edit JSONL files directly.
- `recommendation_id` identifies the target rec; `review_event_id` is the idempotency key for events. Outcomes append unconditionally.
- Outcomes that would otherwise orphan on a superseded plan are either re-linked (canonical leaf has a matching-domain rec) or refused (it doesn't) — never silently dropped.
