# post-v0.1.14 agent-state-visibility findings

> **SUPERSEDED for cycle scoping by `reporting/plans/v0_1_15/PLAN.md`
> round-3 (2026-05-03).** Original recommendation argued for v0.1.15
> = mechanical only / v0.1.16 = daily-loop hardening; the maintainer
> restructure folded daily-loop hardening into v0.1.15 (with the
> recorded gate as the ship claim) and pushed maintainability to a
> new v0.1.17 cycle. The "Recommendation: cycle scoping" section
> at the bottom of this doc was rewritten 2026-05-02 evening to
> match.
>
> **W-A predicate is also superseded by PLAN round-3.** The
> "structural insight" section below describes `is_partial_day` as
> derived from "timestamp + meal count + presence-of-target" — that
> was the round-0 phrasing. The round-3 PLAN §2.B splits the signal:
> `is_partial_day` is target-independent; a separate `target_status:
> "present" | "absent" | "unavailable"` enum carries the target
> presence/absence dimension. The F-AV-01 example output below
> (lines 117-138) does not include the round-3 `target_status` field
> or the `weigh_in.reason: "intake_surface_not_yet_implemented"` per
> W-E (per F-PLAN-R2-04 round-2 finding). The PLAN's §2.B output
> contract is the source of truth for implementation; this doc is
> kept for original-finding provenance only.
>
> **F-AV-03 premise is SUPERSEDED by PLAN round-4 (2026-05-03
> evening).** F-AV-03 below (lines 196-223) argues that
> `hai target commit` is "training-target-shaped, not nutrition-
> shaped" and that a NEW `nutrition_target` table is needed. The
> Phase 0 internal sweep against migration `020_target.sql` and
> live state DB evidence (`hai target list --user-id u_local_1
> --all` returning three nutrition rows already on disk) showed
> the premise is wrong: the existing `target` table is domain-
> agnostic, already supports `target_type IN ('calories_kcal',
> 'protein_g', ...)`, already W57-gates commit via
> `cmd_target_commit`, and is already in production use for the
> maintainer's nutrition rows. PLAN round-4 §2.D revises W-C to
> extend the existing `target` table (CHECK adds `'carbs_g'` +
> `'fat_g'`) and ship `hai target nutrition` as a 4-atomic-row
> convenience over the existing table. See
> `reporting/plans/v0_1_15/audit_findings.md` F-PHASE0-01 for
> the full argument and `reporting/plans/v0_1_15/PLAN.md` §2.D
> for the round-4 contract. F-AV-03's "Proposed workstream"
> section below is preserved as original-finding provenance only;
> the implementation contract lives in PLAN §2.D.

Surfaced 2026-05-02 during a maintainer-as-user morning session
(exam-week nutrition planning + leg/back gym session intake). The
session exposed a class of bugs where the agent (Claude in this case)
made the same mistakes that any agent would make, because the bugs
are structural — there is no agent-readable surface for "what has
already been logged today" or "is this nutrition record a partial-day
running total or a closed end-of-day total."

The maintainer corrected the initial framing — agent-side memory
updates fix Claude on this machine but do nothing for the product.
The findings below are re-cast as code/CLI workstreams that solve the
problem for every agent reading state.

Status: documented for v0.1.16 daily-loop-hardening scope (proposed).
v0.1.15 remains the mechanical W-29/W-30 cli.py split per AGENTS.md
"Settled Decisions"; this finding doc argues that grafting W-A onto
v0.1.15 mid-split creates merge friction and the cleaner shape is a
dedicated v0.1.16 hardening cycle bundling W-A through W-E.

---

## Session context

- Date: 2026-05-02 (Saturday morning, BST 10:03 session start).
- Maintainer goal narration: holding at/above maintenance for ~2 weeks
  during exams, then beginning a lean cut on/around 2026-05-16.
  Daily morning weigh-ins start 2026-05-03.
- Morning ritual (defined in-session): sleep pull → weigh-in →
  breakfast → plan-for-the-day. Rest of day: ad-hoc intake. Saved
  to agent feedback memory.
- Wearable signal: HRV down ~8-10 ms off baseline (91-92 → 83-84),
  RHR drifting up (47→48→49), sleep last night 8.52 h, training load
  consistent (8.4/13.2/11.4). State.db `strength_status` flipped to
  `overreaching` on intake.

The agent's failures during the session, traced to their structural
roots:

1. **Asked "what did you have for breakfast" without checking intake
   state first.** The maintainer had told the model in a prior /clear-
   wiped session and reasonably expected the system to know. The agent
   has feedback-memory rules to check state before asking, but no
   tight CLI surface to do so for nutrition specifically — it would
   have had to read raw `nutrition_intake.jsonl` or stitch
   `hai stats` output. The structural fix is a presence surface, not
   a memory update.

2. **Mis-framed the morning ritual as forward-march at 10am.** The
   agent ran `date`, saw 10:03, picked "morning mode," and structured
   the four anchors as upcoming when the maintainer had already
   eaten breakfast, trained, and had a post-workout snack. The
   structural issue: the agent has no way to query "what has already
   been logged today" before composing the prompt, so every agent
   defaults to forward-march framing.

3. **Wrote partial-day nutrition (~1,344 kcal at 10am) to state
   without proactive warning.** Predictably triggered the partial-day-
   synthesis bug (B1 from 2026-04-27): runtime classified
   `nutrition_status=deficit_caloric`, `protein_sufficiency=very_low`,
   `calorie_balance=high_deficit`. The agent caught it post-hoc when
   reading baselines. The structural issue: there is no `is_partial_day`
   signal in state, no stored daily target to project against, and no
   convention for distinguishing "running total" from "closed total."

---

## Structural insight

Findings F-6 and F-7 from the in-session triage (agent state-check
rule, agent time-aware ritual) dissolve into a single missing CLI
surface: there is no agent-readable "what has been logged today"
answer. Every agent reading state will hit the same blind spot.

The closest existing surface is `hai intake gaps`, which already
takes an evidence snapshot and reports what is *missing*. The
structurally clean fix is extending it (or renaming to
`hai intake state`) to also emit presence tokens. One read surface,
both branches.

The same response should carry partial-day signal —
`intake.nutrition.is_partial_day` derived from timestamp + meal
count + presence-of-target — exposed structurally so both runtime
classification and host-agent narration can branch on it. That
dissolves the partial-day false-flag bug too: the runtime stops
classifying as `high_deficit` when `is_partial_day == true`,
regardless of agent behavior.

---

## F-AV-01: no agent-readable presence surface for today's intake

**Severity:** ship-impact (every agent re-asks the user for
information already in state).

**Shape.** `hai intake gaps` reports gaps; there is no symmetric
report of *presence*. Agents that want to ask "has nutrition been
logged today?" must read raw `nutrition_intake.jsonl`, run
`hai stats --baselines`, or open the SQLite directly — none of which
is the contract the capabilities manifest implies. `hai today` is
recommendation-side. `hai stats` is rolling-window and historical.
The minimal-cost fix is extending `hai intake gaps` to emit a
`present` block alongside the existing `gaps` block.

**Evidence (2026-05-02).** Agent (Claude) asked the maintainer
"what did you have for breakfast" without first checking intake
state. Maintainer response: "I already told you what I had for
fucking breakfast. You should know that." Subsequent
`uv run hai state snapshot --as-of 2026-05-02 --user-id u_local_1`
returned an empty `classified_state.nutrition` block, but the
agent should have queried *before* composing the prompt, not after.

**Proposed workstream (W-A).** Extend `hai intake gaps` with a
`present` block and `is_partial_day` derived signal:

```json
{
  "as_of_date": "2026-05-02",
  "user_id": "u_local_1",
  "gaps": [...],
  "present": {
    "nutrition": {
      "logged": true,
      "submission_id": "m_nut_2026-05-02_091721305236",
      "meals_count": 2,
      "is_partial_day": true,
      "is_partial_day_reason": "timestamp 10:17 < end-of-day cutoff 18:00"
    },
    "gym": {
      "logged": true,
      "session_id": "leg_back_2026-05-02",
      "set_count": 11
    },
    "weigh_in": { "logged": false },
    "readiness": { "logged": false },
    "sleep": { "logged": true, "source": "intervals_icu" }
  }
}
```

Expose via capabilities manifest. No schema change, pure read-side.

**Sizing.** Small — one CLI extension + one capabilities-manifest
update + one new test surface for partial-day signal derivation.

---

## F-AV-02: no body-comp / morning weigh-in intake surface

**Severity:** ship-impact (re-raise of B3 from 2026-04-27).

**Shape.** `hai intake` exposes `readiness`, `nutrition`, `stress`,
`gym`, `note` — no `weight` or body-comp. The morning ritual the
maintainer just defined (sleep → weigh-in → breakfast → plan) has
no canonical home for step 2.

**Evidence.** Maintainer 2026-05-02: "I will begin weighing myself
in the mornings starting tomorrow morning." No `hai intake weight`
exists. `hai intake readiness` accepts a weight field per its help
text — but body weight is not a readiness signal, and conflating
the two muddles the schema.

**Proposed workstream (W-B).** New `hai intake weight --kg <X>
--as-of <Y>` plus a `body_comp` table in state.db. Optional: extend
the capabilities manifest body-comp surface to include trend reads
(`hai stats --domain body-comp` showing 7-day moving average).

**Sizing.** Small-medium — one new command + one new schema table +
migration + one new domain pull surface (or just direct intake).

---

## F-AV-03: no daily nutrition target commit surface

**Severity:** high (pre-req for W-D partial-day fix).

**Shape.** `hai intent commit` covers training intent. `hai target
commit` exists but is training-target-shaped, not nutrition-shaped.
There is no equivalent for "this is my daily macro target while
I'm in this phase" — so partial-day intake has no reference to
project against. The runtime sees 1,344 kcal at 10am with no
target context and the only honest classification is "way below
some implicit number," which the band system reports as
`high_deficit`.

**Evidence.** 2026-05-02 in-session — agent quoted estimated
maintenance brackets (2,850-3,250 kcal) and a Phase 1 target
(~3,000 kcal). None of this was stored in state. State has no
`nutrition_target` row. There is no schema for one.

**Proposed workstream (W-C).** New `hai target nutrition --kcal <X>
--protein-g <P> --carbs-g <C> --fat-g <F> --phase <name>
--effective-from <date>` plus a `nutrition_target` table.
**Must be user-gated per W57** — the agent can propose, the user
must commit. Phase changes (cut → maintain → bulk → cut) commit a
new row; the latest non-superseded row is the active target.

**Sizing.** Medium — new command + new table + W57 gate + capabilities
manifest update + integration with W-D below.

---

## F-AV-04: partial-day nutrition synthesis false flag

**Severity:** ship-impact (re-raise of B1 from 2026-04-27).

**Shape.** Mid-day nutrition intake gets classified as if it were a
closed end-of-day total. Bands flip to `high_deficit` /
`very_low protein`. Daily synthesis would recommend a recovery /
nutrition escalation against this fake deficit if invoked pre-cutoff.

**Evidence (2026-05-02).** After writing 1,344 kcal at 10am, baselines
showed:

```
## nutrition
- calorie_balance_band: high_deficit
- nutrition_status: deficit_caloric
- protein_sufficiency_band: very_low
```

This is the entire day's classification flipping to deficit-state on
breakfast-only data. Untreated, every morning briefing produces the
same false flag for any user logging breakfast before 10am.

**Proposed workstream (W-D).** Two-arm fix gated on W-C presence:

- **Arm 1 (no target, partial-day):** suppress nutrition
  classification — emit `nutrition_status=insufficient_data` with
  reason `partial_day_no_target`. The runtime explicitly refuses to
  classify rather than misclassifying.
- **Arm 2 (target present, partial-day):** project end-of-day from
  `intake_so_far + (target - intake_so_far) * (remaining_day_fraction)`
  and classify against the projection. Surface the projection
  separately from observed intake in `hai explain`.

`is_partial_day` derives from W-A signal. `--running-total` flag on
`hai intake nutrition` is an alternative entry point if auto-detection
is uncertain.

**Sizing.** Medium — touches `domains/nutrition/classify.py` +
`synthesis_policy.py` + ~5 tests + audit-chain rendering update.

---

## F-AV-05: morning-ritual flow is agent-narrated, not packaged

**Severity:** medium (UX trip-hazard, becomes acute once W-A through
W-D land).

**Shape.** The four-step morning cycle is encoded only as agent
behavior (now in agent feedback memory). No `hai morning` bundle, no
packaged morning-ritual skill. Every agent re-narrates the flow,
which means every agent has its own version of the bug surface.

**Proposed workstream (W-E).** Two parts:

- Update the existing `merge-human-inputs` skill to explicitly consume
  W-A presence tokens before composing prompts (skills are how
  prose-level behavior is encoded for any host agent).
- Optionally ship a packaged `morning-ritual` skill that orchestrates
  pull → weigh-in prompt → breakfast prompt → plan, branching on
  W-A presence to choose recap-first vs forward-march framing.

**Sizing.** Small (skill update); medium (new packaged skill).

---

## Recommendation: cycle scoping (UPDATED 2026-05-02 evening)

This section was rewritten after the 2026-05-02 evening
maintainer-as-user session reproduced the same findings AND
surfaced one new runtime bug (W-GYM-SETID — gym set-id PK collision).
The maintainer chose a different scope shape from the prior
recommendation.

**Final cycle assignment:**

- **v0.1.15** ("foreign-user candidate package + recorded gate")
  ships W-A + W-C + W-D arm-1 + W-E + W-GYM-SETID + F-PV14-01 + the
  W-2U-GATE recorded session itself. The user-facing daily-loop
  hardening lands here so the gate test is meaningful. Tier:
  substantive. See `reporting/plans/v0_1_15/PLAN.md`.
- **v0.1.16** ("empirical post-gate bug fixes") stays reserved for
  whatever the W-2U-GATE recorded session surfaces. P0 closed inline
  in v0.1.15; P1 named-deferred or closed in v0.1.16.
- **v0.1.17** ("maintainability + eval substrate consolidation")
  takes W-29 cli.py split + W-30 + W-AH-2 / W-AI-2 / W-AM-2 / W-Vb-4
  + F-PV14-02 + W-B + W-D arm-2. These are maintainer-side concerns
  with no foreign-user impact and were originally bundled into
  v0.1.15 round-0. The v0.1.15 round-0 self-audit cut them per the
  second-user-objective optimization; see
  `reporting/plans/v0_1_17/README.md` and `v0_1_15/PLAN.md` §1.4.

**Why this differs from the prior recommendation.** The original
"v0.1.15 mechanical only / v0.1.16 daily-loop hardening" framing
assumed the foreign-user gate session would be a separate cycle
(v0.1.16's ship claim). The 2026-05-02 evening restructure folded
the gate session into the same cycle as the user-facing fixes, so
"v0.1.16 = gate" became "v0.1.15 = gate." That cascaded the
maintainability + eval work to v0.1.17 (new) so v0.1.16 could stay
exclusively reserved for empirical post-gate fixes. Same total
cycle count; the gate ship-claim moves one release earlier.

The prior recommendation's coupling argument (W-A through W-D
share architecture) still holds and is preserved as the v0.1.15
PLAN's Phase 1+2 sequencing rationale. The prior recommendation's
cli.py merge-friction argument is also preserved — and is exactly
why W-29 lives in v0.1.17 (separate cycle) rather than alongside
W-A-E in v0.1.15.

---

## Cross-references

- AGENTS.md "Settled Decisions" — W-29/W-30 destination
- `project_morning_briefing_v0_1_x_bugs_2026-04-27.md` (memory) —
  B1 partial-day, B3 no body-comp surface (this doc re-raises both)
- `feedback_partial_day_nutrition_synthesis.md` (memory) —
  agent-side workaround that this doc proposes replacing with code
- `feedback_check_state_before_asking.md` (memory) — agent-side rule
  that W-A makes mechanically enforceable
- `feedback_daily_cycle_morning_ritual.md` (memory, 2026-05-02) —
  defines the four-step cycle that W-A through W-E support
- `reporting/plans/post_v0_1_14/carry_over_findings.md` —
  unrelated v0.1.15 carry-over (CSV-fixture isolation finding)
