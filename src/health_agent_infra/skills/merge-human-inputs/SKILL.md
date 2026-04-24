---
name: merge-human-inputs
description: Partition unstructured user narration into the typed `hai intake` commands the runtime expects. Use when the user volunteers information outside a form — readiness, gym sets, nutrition, subjective stress, or free-text context. Also drives the session-start gap-filling protocol: read `hai intake gaps`, compose ONE consolidated question, route the answer. You route; you do not interpret.
allowed-tools: Read, Write, Bash(hai pull *), Bash(hai intake *)
disable-model-invocation: false
---

# Merge Human Inputs

You take unstructured human input — narration, transcribed human speech, half-typed answers — and route it into typed `hai intake <kind>` calls. Three ground rules govern everything below:

1. **Structured if it fits, free-text note otherwise.** If the user gives values that match a structured intake's required fields, use that intake. If they don't, log a note. Never invent numbers to fill a typed slot.
2. **You partition, you do not interpret.** Classification (recovery state bands, action selection) belongs to the recovery-readiness skill. You move bytes from narration into the right intake command and ask for clarification when needed.
3. **Ask once, not many times.** At session start, read `hai intake gaps` first and compose ONE consolidated question that covers every gating gap. Drip-feeding is a bug, not a feature.

## Session-start gap-filling protocol

**This runs before any domain-skill invocation.** It is the low-friction entry point: the agent learns what the runtime needs from the user, asks once, then produces recommendations.

### Step 1 — enumerate gaps

```bash
hai intake gaps --as-of <today> --user-id <u> --evidence-json <hai clean output>
```

The JSON response carries:

```json
{
  "gaps": [
    {
      "domain": "recovery",
      "missing_field": "manual_checkin_missing",
      "field_description": "morning self-report: soreness ..., energy ..., planned session ...",
      "intake_command": "hai intake readiness",
      "intake_args_template": "--soreness <low|moderate|high> --energy <low|moderate|high> --planned-session-type <str> [--active-goal <str>]",
      "blocks_coverage": true,
      "priority": 1
    },
    ...
  ],
  "gap_count": 4,
  "gating_gap_count": 4
}
```

When `gap_count` is 0, skip the rest of this protocol. Synthesize directly.

### Step 2 — compose ONE natural question

Read the `field_description` and `domain` of each gap (priority-1 first; defer priority-2 like nutrition to end-of-day if it's morning). Compose a single question in YOUR voice that covers the gating gaps in one exchange. Do NOT copy `field_description` verbatim — it's raw inventory, not conversation. Examples:

- 4 gaps (recovery + strength + stress + nutrition): "Quick morning check-in: how's your soreness + energy (low/mod/high each), what are you training today, and how stressed are you feeling on 1–10? Nutrition we can log after dinner."
- 1 gap (recovery only): "How's your body today — soreness, energy, and what are you planning?"
- 0 gaps: don't ask anything.

### Step 3 — parse the free-text answer

Use the decision table below to route each piece of the user's answer to the right `hai intake <X>` command. If something is ambiguous, ask ONE targeted follow-up (never a wall).

### Step 4 — retry synthesis

After the intakes land, rerun `hai daily --skip-pull --supersede` so the updated evidence feeds synthesis. The plan supersedes cleanly via D1 revision semantics.

### Session-end gap-fill (nutrition primarily)

Priority-2 gaps (nutrition) belong at end-of-day, not morning. When the user says "I'm done eating for the day" or a similar cue, run `hai intake gaps` again; nutrition will still be open; log then synthesize-supersede.

## Available intake surface

## Available intake surface

| Command | Purpose | Required fields | Optional |
|---|---|---|---|
| `hai intake gaps` | **Read-only.** Enumerate user-closeable intake gaps in the snapshot; the agent reads this at session start to drive the consolidated-question protocol above. | `--as-of --user-id --evidence-json` | `--db-path` |
| `hai intake readiness` | Subjective pre-session check (primary hot path) | `--soreness {low\|moderate\|high}` `--energy {low\|moderate\|high}` `--planned-session-type` | `--active-goal` `--as-of` |
| `hai intake gym` | Resistance-training sets | `--session-id --exercise --set-number --weight-kg --reps` (or `--session-json`) | `--session-name --notes --rpe --tags --as-of` |
| `hai intake nutrition` | Daily nutrition aggregate | `--calories --protein-g --carbs-g --fat-g` | `--hydration-l --meals-count --as-of` |
| `hai intake stress` | Subjective stress (1–5) | `--score {1,2,3,4,5}` | `--tags --as-of` |
| `hai intake note` | Free-text context (catchall) | `--text` | `--tags --recorded-at --as-of` |

All mutating intakes accept `--user-id`, `--ingest-actor` (`hai_cli_direct` or `claude_agent_v1` — use `claude_agent_v1` when you mediate), `--base-dir`, and `--db-path`.

## The hybrid rule (decision table)

This is the hybrid rule. Lead with the structured form when it fits; fall back to `hai intake note` when it doesn't. **Never fabricate numbers to fit a structured slot** — ask for the missing piece, or take the note.

| User narration | Route to | Why |
|---|---|---|
| "Today: 2200 cals, 180p, 250c, 70f" | `hai intake nutrition --calories 2200 --protein-g 180 --carbs-g 250 --fat-g 70` | Complete macros provided. |
| "Big lunch, lots of carbs" | `hai intake note --text "big lunch, lots of carbs"` | No numbers; cannot fabricate macros. |
| "Lunch was around 700 cals" | Ask: "Got the rest of the day's totals? If not I'll log this as a note." | Partial macros — pick one path, don't put a NULL into a structured field with required friends. |
| "Bench 80kg 5×3" | `hai intake gym --session-id bench_<date> --session-name "Bench" --exercise "Bench Press" --set-number 1 --weight-kg 80 --reps 5` (then again for sets 2 and 3) | Concrete sets. Use bulk JSON when ≥3 sets. |
| "Did some pushups" | `hai intake note --text "did some pushups (count not specified)"` | No reps/weight given. |
| "Stressed about deadline, like a 4" | `hai intake stress --score 4 --tags work,deadline` | Numeric score in 1–5 range. |
| "Pretty stressed today" | Ask: "On 1-5, where 5 is severe stress, what would you say?" Then `hai intake stress --score N`. | No score given. |
| "Slept badly, anxious dreams" | `hai intake note --text "slept badly, anxious dreams"` | Subjective with no structured slot. |
| "Soreness 6/10, energy 4/10, planned a hard run, building 5k base" | `hai intake readiness --soreness moderate --energy moderate --planned-session-type hard --active-goal 5k_pr_build` | All 4 fields given. Map 0–10 to bands: 0–3 low, 4–6 moderate, 7+ high. |
| "Coffee at 9pm, regret it" | `hai intake note --text "coffee at 9pm, regret it" --tags caffeine,sleep` | Context note; tags help the agent find it later. |

When in doubt: **note it.** A note never loses information. A wrong structured intake hides it inside a typed slot the agent reasons over.

## Hot path: readiness intake before `hai pull`

The daily flow expects readiness before a `hai pull`. Walk the user through the four fields, then chain:

```bash
hai intake readiness --soreness moderate --energy moderate \
                     --planned-session-type hard --active-goal 5k_pr_build \
                     > /tmp/mr.json
hai pull --date 2026-04-17 --manual-readiness-json /tmp/mr.json \
         > /tmp/evidence.json
hai clean --evidence-json /tmp/evidence.json --db-path … \
          > /tmp/cleaned.json
```

Note: state-DB projection is owned by `hai clean`, not `hai pull`. `hai pull` only emits Garmin evidence on stdout; `hai clean` reads that JSON, normalises it, and projects into the local SQLite store via the optional `--db-path`.

Field mapping discipline:

- **Soreness / energy**: ask for a 0–10 number, then map: 0–3 → `low`, 4–6 → `moderate`, 7+ → `high`. If the user gives a band directly ("kinda sore"), confirm: "Calling that moderate, OK?"
- **Planned session**: free text. Encourage one of `easy`, `moderate`, `hard`, `intervals`, `race`, `rest` so the recovery-readiness skill can match. "Going for a 10k tempo" → `hard`. "Mobility only" → `rest` (unless user clarifies they mean light effort).
- **Active goal**: free text in the user's framing. Don't rename `feel_good` to `general_wellbeing`. The agent reads this verbatim.

## Same-day correction rule

Every intake command except `note` treats a re-run for the same `(as_of_date, user_id)` as a **correction**:

- Stress / nutrition: a fresh raw row is appended with `supersedes_submission_id` pointing at the prior tail; `accepted_*` UPSERTs with `corrected_at` set.
- Gym: deterministic `set_id` per `(session_id, set_number)` makes re-running a set a no-op; corrections require an explicit `--session-json` with a fresh set_id and `supersedes_set_id`. (V1 doesn't expose per-set CLI correction flags.)
- Notes: append-only — there's no correction in v1; new notes are independent rows.

If the user says "actually I miscounted, it was 2400 cals not 2200," you simply re-run the nutrition intake with the corrected numbers. The runtime handles the chain.

## What you must never do

- **Fabricate a structured value.** "Big lunch" is not 800 calories. "A bit sore" is not `moderate`. Ask, or note it.
- **Silently reclassify the user's framing.** If they say `active_goal=feel_good`, that's the goal. Don't sanitize it to `general_wellbeing`.
- **Add signals the user didn't report.** If they mentioned sleep but not HRV, don't write an HRV value anywhere.
- **Route medical or diagnostic language into intake slots.** "I think I have COVID" — refuse to log that as recovery data and point to a clinician. Follow the safety skill's rules.
- **Run admin / operator commands.** These are user-only; never invoke them yourself:
  - `hai state init`
  - `hai state migrate`
  - `hai state reproject`
  - `hai setup-skills`
  - any direct SQLite access
  
  If the user says "rebuild my DB" or "wipe the projection tables," explain that's an operator action and surface the exact command for them to run themselves.

## Confirmation pattern

Before invoking a structured intake, confirm in one short sentence:

> "I'll log nutrition: 2200 cals / 180p / 250c / 70f for today. Confirm?"

Then run the command. If the user pushes back on a value, re-confirm with their correction (which becomes a correction-chain raw row, not a new entry).

For `hai intake note`, you don't need confirmation — notes are non-destructive and the user wrote the text themselves.

## When you're uncertain

Ask **one** targeted question, not a wall of options. "Is this about today's session or yesterday's?" or "On a 1–5 stress scale, what would you say?" beats listing every possible interpretation. The user's bandwidth is the bottleneck.
