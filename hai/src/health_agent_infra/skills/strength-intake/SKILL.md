---
name: strength-intake
description: Convert a user's narrated strength session into structured `hai intake gym` calls. Judgment-only — all name resolution and parsing lives in code.
allowed-tools: Read, Write, Bash(hai exercise search *), Bash(hai intake gym *)
when_to_use: >
  When the user describes a resistance-training session in free text
  ("back squats 5×5 at 100kg, then bench 4×5 at 80kg") and the
  harness has a state DB available. Not for numeric dumps via
  `hai intake gym --session-json` — those are already structured.
---

# strength-intake

## What you own

You own **disambiguation and clarification**, not parsing or matching.

- Ask the user the minimum number of questions needed to resolve
  ambiguity.
- When the user confirms a match, invoke the CLI with the confirmed
  exercise name.
- When the user declines a catalogue extension, leave the set as
  free-text — the projector will surface it in
  `unmatched_exercise_tokens_json` so the user can decide later.

## What you do NOT own

The following lives in code (`domains/strength/taxonomy_match.py` +
`core/state/projectors/strength.py`). Do not reimplement any of it
here:

- Case-folding, whitespace normalisation, alias vs canonical lookup.
- Ranking / scoring of search candidates.
- Any arithmetic that decides whether a match is good enough to
  stamp `exercise_id`.
- Deciding what counts as "heavy" / "hard" / "lower-body" / etc. —
  those are classifier concerns (`domains/strength/classify.py`).
- Writing any structured field beyond what `hai intake gym` accepts.

If you find yourself writing a regex, a threshold, or a ranking rule,
stop and file it as a code change instead.

## Protocol

1. **Extract the raw references** from the user's message: each
   mention of an exercise plus its set structure (sets × reps × weight,
   optional RPE).

2. **Resolve each exercise** by calling:
   ```
   hai exercise search --query "<user's phrasing>" --limit 5
   ```
   Inspect the `hits` array:
   - If the top hit has `match_reason == "exact_canonical"` or
     `match_reason == "exact_alias"`, treat the match as confirmed.
   - If the top hit is a substring/token match and the score gap to
     the next hit is large, still confirm it by echoing the canonical
     name back to the user in your next message.
   - If multiple hits are close in score, present the top 3 canonical
     names as options and ask the user which one they meant. Do NOT
     guess.
   - If there are no hits at all, tell the user the lift is not in
     the catalogue and ask whether they want to:
     (a) proceed with the free-text name (projector will flag it in
     `unmatched_exercise_tokens_json`), or
     (b) skip the set.

3. **Parse the set structure** into per-set tuples. The CLI already
   accepts either mode — pick whichever fits:
   - `--session-json` bulk mode when the session has multiple
     exercises or many sets.
   - Per-set flags when the session is a single exercise with one
     or two sets.

4. **Invoke the CLI** with the confirmed names. Example bulk invocation:
   ```
   hai intake gym --session-json ./session.json \
     --as-of 2026-04-18 --user-id u_primary \
     --base-dir ~/health/writebacks \
     --db-path ~/Library/Application\ Support/health_agent_infra/state.db
   ```
   where `session.json` is:
   ```json
   {
     "session_id": "2026-04-18-legs",
     "session_name": "Legs",
     "as_of_date": "2026-04-18",
     "sets": [
       {"set_number": 1, "exercise_name": "Back Squat", "weight_kg": 100.0, "reps": 5},
       {"set_number": 2, "exercise_name": "Back Squat", "weight_kg": 110.0, "reps": 5},
       ...
     ]
   }
   ```

5. **Echo the result** back to the user. Mention:
   - Which exercises resolved cleanly (top hit, `exact_*` match).
   - Which exercises you had to ask about (with the disambiguation
     you applied).
   - Any sets left as free-text so the user can decide on a catalogue
     extension later.

## Never do

- Never invent numeric values the user didn't state. If RPE is
  missing, leave it NULL — the optional field stays NULL in the
  JSONL and the DB.
- Never retroactively correct a prior set with a different
  exercise_id without the user asking. Corrections ride the
  `supersedes_set_id` chain explicitly.
- Never call `hai exercise search` in a loop to auto-expand the
  taxonomy. User-defined entries arrive only through a deliberate
  `hai intake exercise` invocation the user approves.
- Never stamp an `exercise_id` yourself. You hand free-text to
  `hai intake gym`; the CLI (via the code-owned matcher) stamps the
  id when the match is unambiguous and leaves NULL otherwise.

## Confidence tiers

When echoing results back, mirror the code-owned tiers from
`ExerciseMatch`:

- `exact` — canonical name match, silent (no confirmation needed).
- `alias` — alias match, silent unless the alias is plausibly
  ambiguous in context.
- `ambiguous` — multiple taxonomy rows share the alias; surface the
  alternatives and ask.
- `no_match` — unresolved; surface the user's raw phrasing and ask
  whether to leave as free-text or skip.

The tiers are your vocabulary, not your decision surface — the code
has already decided which tier applies.
