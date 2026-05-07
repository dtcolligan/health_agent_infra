# W52 W-EXPLAIN-UX-CARRY obligation disposition tracker

Per PLAN §2.D acceptance #7 + §2.K. This file tracks disposition for
every prose obligation enumerated in
`reporting/docs/archive/cycle_artifacts/explain_ux_review_2026_05.md`
under "v0.2.0 W52 prose obligations" (lines 191-248).

Each obligation has one of four named dispositions:
`implemented-in-W52` / `deferred-to-v0.2.1` / `deferred-to-v0.3` /
`out-of-scope-with-reason`.

Cycle: v0.2.0 (Wave 2 gateway). Authored 2026-05-07 alongside W52
step 4 commit. See `PLAN.md` §2.D for the parent contract.

---

## Obligation table

| # | F-EXPLAIN | Disposition | Implementation site | Test asserting compliance |
|---|---|---|---|---|
| 1 | F-EXPLAIN-01 — Rule IDs opaque | **implemented-in-W52** | `core/review/prose_builder.py:_rule_phrase` — `public_name_for` is the leading subject; raw rule_id surfaces only in parentheses | `test_review_weekly.py::test_prose_no_xrule_id_outside_parens` |
| 2 | F-EXPLAIN-02 — `phase_a`/`phase_b` unexplained | **implemented-in-W52** | `core/review/prose_builder.py:_phase_a_b_framing` — tier groups produce inline prose ("rules that shaped the recommendation" / "rules that adjusted the result after the skill ran"); raw `phase_a`/`phase_b` strings never appear in atom text | `test_review_weekly.py::test_prose_no_phase_a_b_raw_strings` |
| 3 | F-EXPLAIN-03 — `synthesis_meta` debug | **implemented-in-W52** | `core/review/prose_builder.py` — atom text never contains the literal string `synthesis_meta`; the render layer (step 5) keeps `synthesis_meta` in JSON only | `test_review_weekly.py::test_prose_no_synthesis_meta_string` |
| 4 | F-EXPLAIN-04 (P0) — Caveat tokens opaque | **implemented-in-W52** | `core/explain/caveat_translations.py` — registry covers all currently-emitted `reason_token` values across the 6 domains + the 9 X-rule firings + nutrition X2 templates; fallback humanises any future token. `core/review/prose_builder.py:_summarise_rationale` routes every rationale through `translate_caveat` | `test_review_weekly.py::test_prose_no_raw_caveat_tokens` + `test_caveat_translations.py` registry coverage |
| 5 | F-EXPLAIN-05 — User goal not echoed | **implemented-in-W52** | `core/review/prose_builder.py:load_primary_goal` reads from `user_memory` (key='primary_goal', archived_at IS NULL); `_build_header_section` emits goal echo as the first noun phrase of the body. Honest abstain when no goal is set | `test_review_weekly.py::test_prose_header_echoes_primary_goal` |
| 6 | F-EXPLAIN-07 — Locators referenced in prose | **implemented-in-W52** | `core/review/prose_builder.py:_format_locator_lead_in` — every per-recommendation atom whose `evidence_locators` is non-empty gets a "Looking at <metric> on <date list>: …" prose lead-in that names the locator's `pk.as_of_date` field | `test_review_weekly.py::test_prose_locator_cited_lead_in` |

Six obligations total — all six are disposed `implemented-in-W52`.
No deferral; the original review doc explicitly noted these as
"v0.2.0 W52 prose obligations" with no carry-forward shape.

---

## Carry-forward to v0.1.15-W-2U-GATE-foreign-user-pass

The review doc separately names four items (lines 249-278) that
benefit from re-testing against an actual foreign user. Per **D16**
(post-v0.1.18 W-2U-GATE-SPLIT) the foreign-user empirical work is
opportunistic-not-blocking from v0.2.0 forward; the v0.1.18
post-cycle session closed W-2U-INSTALL but did not re-test these
four items against W52 prose (W52 didn't exist yet).

| F-EXPLAIN item | Status |
|---|---|
| F-EXPLAIN-01 (rule_id opaque hypothesis) | maintainer-substitute confirmed; foreign-user re-test deferred to v0.4 review per D16 |
| F-EXPLAIN-04 (P0 caveat tokens) | maintainer-substitute marked P0; mechanical assertion ships in W52; foreign-user re-test deferred to v0.4 review per D16 |
| F-EXPLAIN-05 (goal echo as load-bearing) | maintainer-substitute hypothesis; W52 implements; foreign-user re-test deferred to v0.4 review per D16 |
| F-EXPLAIN-07 (locator legibility, no R6 in maintainer state) | mechanical assertion ships; foreign-user re-test deferred to v0.4 review per D16 |

These four items become the explicit walk-through script for the
v0.4 review when MCP read-surface decisions force foreign-user
evidence (per D16 re-evaluation gate).

---

## Coverage parity invariant

The `core/explain/caveat_translations.py` registry MUST stay in
parity with the runtime's actually-emitted `reason_token` set.
`test_caveat_translations.py` enumerates every `reason_token` it
finds via static grep across `src/health_agent_infra/domains/` and
`src/health_agent_infra/core/synthesis*.py`, and asserts every
non-templated token has a non-default registry entry. New domain or
X-rule tokens that ship without a registry entry break the test —
the obligation hook fires at PR-review time, not at user read time.
