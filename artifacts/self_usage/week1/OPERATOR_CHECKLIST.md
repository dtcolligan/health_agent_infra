# Week 1 self-usage operator checklist

This checklist is the day-flow for one honest same-day Health Lab self-usage run using current repo surfaces only.

Preferred repo-root wrapper after the runtime files exist:
```bash
python3 scripts/run_self_usage_day.py \
  --date "$DATE" \
  --user-id "$USER_ID" \
  --voice-note-payload-path "$PROOF_DIR/voice_note_payload.json" \
  --recommendation-payload-path artifacts/self_usage/templates/recommendation_payload_example_2026-04-10.json \
  --judgment-label useful \
  --action-taken "Chose a lighter evening and skipped extra training load." \
  --why "The recommendation matched the low-energy and soreness context and was specific enough to act on immediately." \
  --caveat "No passive wearable or sleep-duration signals were present in this same-day proof run." \
  --time-cost-note "About 10 minutes including one payload review." \
  --friction-points "manual recommendation payload review" "proof copy now automated"
```
The runner keeps recommendation authorship explicit, validates evidence refs against the day context before acceptance, copies the proof bundle, and records compact friction/usefulness capture in `artifacts/self_usage/week1/YYYY-MM-DD/runner_capture_YYYY-MM-DD.json`.

## Fixed conventions
- user_id: `user_dom`
- runtime directory: `data/health/`
- dated bundle: `data/health/shared_input_bundle_YYYY-MM-DD.json`
- dated context: `data/health/agent_readable_daily_context_YYYY-MM-DD.json`
- dated recommendation: `data/health/agent_recommendation_YYYY-MM-DD.json`
- proof bundle root: `artifacts/self_usage/week1/YYYY-MM-DD/`
- gym logging rule: log gym only in `data/health/manual_gym_sessions.json`, then add a same-day gym note in the judgment log if training occurred

## 0. Set the day once
```bash
export DATE=2026-04-10
export USER_ID=user_dom
export HEALTH_DIR=data/health
export PROOF_DIR=artifacts/self_usage/week1/$DATE
mkdir -p "$PROOF_DIR/screenshots"
```

## 1. Bootstrap the dated bundle if it does not exist yet
```bash
python3 -m health_model.agent_bundle_cli init   --bundle-path "$HEALTH_DIR/shared_input_bundle_${DATE}.json"   --user-id "$USER_ID"   --date "$DATE"
```

## 2. Log same-day hydration
```bash
python3 -m health_model.agent_submit_cli hydration   --bundle-path "$HEALTH_DIR/shared_input_bundle_${DATE}.json"   --output-dir "$HEALTH_DIR"   --user-id "$USER_ID"   --date "$DATE"   --collected-at "${DATE}T09:15:00+01:00"   --ingested-at "${DATE}T09:15:05+01:00"   --raw-location "healthlab://manual/hydration/${DATE}/morning"   --confidence-score 0.99   --completeness-state complete   --amount-ml 600   --beverage-type water   --notes "Morning bottle"
```

## 3. Log one same-day meal note
```bash
python3 -m health_model.agent_submit_cli meal   --bundle-path "$HEALTH_DIR/shared_input_bundle_${DATE}.json"   --output-dir "$HEALTH_DIR"   --user-id "$USER_ID"   --date "$DATE"   --collected-at "${DATE}T13:10:00+01:00"   --ingested-at "${DATE}T13:10:10+01:00"   --raw-location "healthlab://manual/nutrition/${DATE}/lunch"   --confidence-score 0.95   --completeness-state complete   --note-text "Chicken wrap, yogurt, and fruit after the gym."   --meal-label lunch   --estimated true
```

## 4. Optionally submit one same-day voice note
Use the checked-in example payload as a starting point, then edit timestamps and transcript truthfully for the day.
```bash
python3 -m health_model.agent_voice_note_cli submit   --bundle-path "$HEALTH_DIR/shared_input_bundle_${DATE}.json"   --output-dir "$HEALTH_DIR"   --user-id "$USER_ID"   --date "$DATE"   --payload-path "$PROOF_DIR/voice_note_payload.json"
```

## 5. Read back the dated context artifact
```bash
python3 -m health_model.agent_context_cli get   --artifact-path "$HEALTH_DIR/agent_readable_daily_context_${DATE}.json"   --user-id "$USER_ID"   --date "$DATE"
```

## 6. Validate and write one recommendation artifact
Start from `artifacts/self_usage/templates/recommendation_payload_example_2026-04-10.json`, then update the date and evidence refs if your live context differs.
```bash
python3 -m health_model.agent_recommendation_cli create   --output-dir "$HEALTH_DIR"   --payload-path artifacts/self_usage/templates/recommendation_payload_example_2026-04-10.json
```

## 7. Record judgment immediately
Append one row using `artifacts/self_usage/templates/judgment_log_template.csv` as the shape.
- label must be one of: `useful`, `obvious`, `wrong`, `ignored`
- keep why to 1 to 2 honest lines
- if you trained today, add the gym note here and confirm gym logging stayed in `data/health/manual_gym_sessions.json`

## 8. Copy proof artifacts into the day bundle
```bash
cp "$HEALTH_DIR/shared_input_bundle_${DATE}.json" "$PROOF_DIR/"
cp "$HEALTH_DIR/agent_readable_daily_context_${DATE}.json" "$PROOF_DIR/"
cp "$HEALTH_DIR/agent_recommendation_${DATE}.json" "$PROOF_DIR/"
```
Then add or update:
- `$PROOF_DIR/judgment_log.csv`
- optional screenshot or JSON excerpt under `$PROOF_DIR/screenshots/`

## Done when
- the dated bundle, context, and recommendation exist under `data/health/`
- the copied bundle, copied context, copied recommendation, and judgment log row exist under `artifacts/self_usage/week1/$DATE/`
- the day can be understood from checked-in files without hidden steps
