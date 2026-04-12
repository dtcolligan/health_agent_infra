# manual subjective recovery v1

This document freezes the bounded v1 contract for manual subjective recovery inputs.

## Scope

In scope for this slice:
- manual-form or voice-note subjective daily recovery capture
- one normalized `subjective_daily_input` per source artifact and day when reconstruction is deterministic
- explicit stable IDs, provenance, confidence, and conflict status
- downstream `perceived_recovery` as an inspectable derivation only

Out of scope:
- broader manual-input redesign
- snapshot-contract redesign
- treating inferred `perceived_recovery` as source truth

## Stable ID rule

Normalized subjective recovery uses:
- `source_record_id = subjective:<source_artifact_id>:day:<date>`
- `provenance_record_id = provenance:<source_record_id>`

These IDs must be stable on replay of the same source artifact for the same day.

## Canonical `subjective_daily_input`

Required fields for this bounded lane:
- `date`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`
- `energy_self_rating`
- `stress_self_rating`
- `mood_self_rating`
- `perceived_sleep_quality`
- `illness_or_soreness_flag`
- `free_text_summary`
- `confidence_label`
- `confidence_score`

Current normalization in repo maps `SubjectiveDailyEntryModel` to this contract.

## Provenance rule

Every normalized subjective daily output must retain one primary provenance chain back to the originating human-input artifact.

Minimum provenance fields:
- originating artifact ID
- derivation method
- supporting refs when available
- parser version when relevant
- explicit `conflict_status`

## Downstream derivation rule

`perceived_recovery` remains downstream-only in this slice.

It may be grounded from an explicit canonical subjective event when present, or inferred downstream from subjective sleep-quality and soreness signals.

If inferred:
- it must stay marked as derived or inferred downstream
- it must not become a new canonical source field in `subjective_daily_input`
- the daily context must keep the derivation inspectable
