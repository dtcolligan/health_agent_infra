# WP-E lock evidence — 2026-07-05

- PILOT_PROTOCOL.md final SHA-256 (post-§20, post-table-refresh):
  `4f4da63b49a8083215bc17e906d5ad668eb042b369e1c14eb488748efdc17f49`
- Mechanical lock checklist: `lock_checklist_wp_e_2026-07-05.json`
  (lock_hashes pass; l7_turn_budget pass; schema_json_parse pass;
  scorer_config provenance+frozen pass; untold_leak_scan pass over all 15
  untold tasks; context_window_budget: run conditions pass/pass/pass +
  the below-floor control 'disclosed' per its pre-registered overflow).
- Live API preflight (2026-07-05, direct chat completions, max_tokens=4,
  each run condition's full vendor decoding settings): all four run
  conditions returned HTTP 200 with all parameters accepted, including
  the near-floor condition's chat_template_kwargs thinking-disable and
  presence_penalty. This supersedes the checklist's built-in read-only
  probe, which reports 'pending' solely because legacy provenance
  conditions (Fireworks/Anthropic) have no live keys.
- Operate-floor canary threshold ratified by Dom: 0.5.
- Main-sweep execution mode ratified by Dom: straight through.
- Together balance at lock: $40.10; auto-recharge unset; provider pauses
  usage at $0.
