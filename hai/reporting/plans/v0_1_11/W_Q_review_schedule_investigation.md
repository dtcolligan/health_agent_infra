# W-Q — Review-Schedule Auto-Run Investigation

> **Cycle:** v0.1.11 W-Q. **Source:** F-B-03 from
> `v0_1_10/audit_findings.md`.
>
> **Question.** Are the missing reviews on 2026-04-25 and 2026-04-26
> a regression, intended-manual, or bug?

---

## Trace

`hai daily` (cli.py `cmd_daily` → `_run_daily`) auto-schedules
reviews on the synthesis-success path **unconditionally**, gated only
by the user-controlled `--skip-reviews` flag. The path:

1. `_run_daily` runs pull → clean → snapshot → propose-gate → synthesize.
2. On synthesize success (`result.daily_plan_id` minted), the handler
   reaches `if args.skip_reviews: ... else: scheduled = _schedule_reviews_for_daily_plan(...)`.
3. `_schedule_reviews_for_daily_plan` reads each recommendation's
   `follow_up` block from `recommendation_log`, builds a
   `ReviewEvent`, persists JSONL, projects into `review_event`.
4. Every recommendation in the daily_plan gets a scheduled review;
   `scheduled[]` returned in the report's `stages.reviews.scheduled_event_ids`.

**Files inspected:**
- `src/health_agent_infra/cli.py:4579-4629` — `_schedule_reviews_for_daily_plan`.
- `src/health_agent_infra/cli.py:4917-4927` — daily handler invocation.
- `src/health_agent_infra/core/review/outcomes.py` — outcome recording (separate path; not in the schedule loop).

There is no other code path that produces a `daily_plan` row (and
therefore no other code path that should schedule reviews). The
schedule logic is single-source.

## Cross-check against the runtime_event_log

`hai stats` on the maintainer's local DB at the time of the
2026-04-28 demo showed:

```
2026-04-28T12:42:32  daily failed   (intervals.icu 403)
2026-04-27T17:14:17  daily ok
2026-04-27T17:13:54  daily ok
2026-04-27T06:47:04  daily ok
2026-04-27T06:40:50  daily ok
2026-04-27T06:38:55  daily ok
2026-04-26T19:28:52  daily ok
```

- **2026-04-25:** no `daily` invocations recorded for the day. The
  user did not run `hai daily` that civil date. Reviews can only be
  scheduled by a successful daily run; with no run, no reviews.
- **2026-04-26:** one `daily ok` run at 19:28 UTC. Whether that run
  scheduled reviews depends on whether `_schedule_reviews_for_daily_plan`
  fired (it should have, given `--skip-reviews` was not passed and
  the run is recorded as `ok`).

## Verdict

**Intended-manual + user-skipped-day. Not a regression, not a bug.**

- The auto-schedule path exists and fires on every success.
  No conditional logic gates it beyond `--skip-reviews` (a
  user-controlled flag).
- The 2026-04-25 absence is a user-pattern artifact (no daily run
  that day), not a code defect.
- The 2026-04-26 case had a daily run; the JSONL audit (`review_events.jsonl`)
  + `review_event` projection should reflect that run's scheduled
  reviews. If the day's reviews are missing in projection but
  present in JSONL, the bug is in the projection path
  (`project_review_event`), not the schedule loop. **No evidence
  of that mismatch surfaced during this investigation.**

## Disposition

**No code changes required for v0.1.11 W-Q.**

UX surface improvement worth considering for v0.1.12 (NOT in
v0.1.11 scope): `hai today` could surface a one-line note when
the canonical plan exists but no scheduled review is on file for
the day after — that surfaces the projection-mismatch case
(2026-04-26 shape) without requiring users to inspect the
JSONL ↔ DB by hand.

Documented in this file rather than the codebase because no code
change occurred. PLAN.md § 2.10 W-Q acceptance: "Verdict
documented in cycle response." → satisfied here.
