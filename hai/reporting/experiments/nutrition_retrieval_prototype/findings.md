# Nutrition retrieval prototype — findings

- Phase: 2.5, Track A
- Session: Claude Opus 4.7, 2026-04-17
- Slice: USDA SR Legacy CSV, 7793 foods (publication 2018-04)
- Retrieval: transparent alias-aware token-overlap heuristic
  (`search.score_match`), locked before queries ran
- Queries: 20, authored blind to the slice

## Headline

**Strict top-1 accuracy: 5/20 = 25%.**
Generous (match + partial): 11/20 = 55%.

Per the plan's gate thresholds, both numbers land in the <60% bucket.

**Recommendation: defer meal-level intake; ship macros-only in Phase 5.**

## Method note on honesty

The heuristic is deliberately simple. A fuzzy-match + synonym + learned-ranker
stack would plausibly lift accuracy significantly. What this gate measures is
the *floor* reachable from the USDA SR Legacy naming convention with a
transparent scorer — i.e. what a v1 implementation would give us without
Phase-5 budget spent on retrieval engineering. That floor is the honest
input to the scope call.

The scoring rubric (from `scoring.json`):
- **match** — top-1 satisfies `expected_intent` (correct category + form)
- **partial** — right food category, wrong specific variant/preparation/brand
- **miss** — wrong food category; using it would misrepresent the meal

Ground truth (`expected_intent`) was written into `queries.json` at query
authoring time, before the slice was downloaded or scored.

## Results per query

| id  | query                              | verdict  | failure mode             |
|-----|------------------------------------|----------|--------------------------|
| q01 | scrambled eggs                     | partial  | preparation              |
| q02 | oatmeal                            | miss     | aliasing                 |
| q03 | greek yogurt                       | partial  | brand_vs_generic         |
| q04 | chobani yogurt                     | match    | —                        |
| q05 | chicken breast                     | partial  | preparation              |
| q06 | grilled chicken                    | miss     | composite_capture        |
| q07 | a cup of rice                      | partial  | preparation              |
| q08 | brown rice                         | miss     | aliasing (word order)    |
| q09 | two slices of whole wheat toast    | miss     | aliasing (toast→bread)   |
| q10 | peanut butter sandwich             | miss     | aliasing                 |
| q11 | banana                             | match    | —                        |
| q12 | apple                              | match    | —                        |
| q13 | protein shake                      | partial  | brand_vs_generic         |
| q14 | coffee with milk                   | partial  | composite_decomposition  |
| q15 | spinach salad                      | miss     | aliasing                 |
| q16 | salmon fillet                      | miss     | aliasing                 |
| q17 | chicken wrap with cucumber         | miss     | composite_ambiguity      |
| q18 | some almonds                       | miss     | tie_break_luck           |
| q19 | avocado toast                      | match    | —                        |
| q20 | broccoli                           | match    | —                        |

Detail per query in `scoring.json`.

## Failure modes, distilled

**Dominant failure class: aliasing between user vocabulary and USDA naming.**
The SR Legacy naming convention is `HEAD_NOUN, modifier, modifier…`. Users
narrate in the opposite order (`modifier HEAD_NOUN`) or use informal aliases
that USDA does not carry:

- `brown rice` → USDA `Rice, brown, long-grain, cooked`. User word-order is
  reversed; the scorer's contiguous-phrase bonus never fires, and ties
  break to whichever CSV row comes first — often a processed product
  (rice cakes, snacks).
- `toast` → USDA `Bread, whole-wheat, ..., toasted`. Users say *toast* as
  a noun; USDA stores it as an adjective on bread.
- `salmon fillet` → USDA `Fish, salmon, Atlantic, ...`. `fillet` as a
  standalone product outranks `Fish, salmon, ... filets` because the
  head-noun `Fish` is generic.
- `almonds` → ties with `Nuts, almonds, dry roasted` at identical score;
  tie break is arbitrary (CSV order), surfaces granola bars.

**Second-order failure class: composite meals.** Multi-food phrases
(`chicken wrap with cucumber`, `peanut butter sandwich`,
`coffee with milk`) have no single right answer — they need to be
segmented into their constituent foods *before* retrieval. The heuristic
as built does one lookup per phrase and returns a single food, which is
structurally wrong for these cases.

**Third-order failure class: brand and preparation drift.** Plain queries
(`greek yogurt`, `protein shake`) return a branded or otherwise specific
variant (Chobani apricot, SlimFast RTD) rather than a generic plain entry.
The canonical exists in the slice; the scorer can't tell that a branded
flavoured variant is a worse answer than a plain one. For macronutrient
estimation the drift is small; for micronutrients it is not.

**What works.** Single-token head-noun matches with plural-'s'
normalization (`banana`, `apple`, `broccoli`) are clean. When the user
says the USDA head noun exactly and USDA carries a `raw` variant, the
heuristic nails it. Five of the five clean matches fall in this pattern;
everything more complex degrades.

## What would need to change to reach ≥60% (let alone ≥80%)

1. **Synonym / alias layer** — `toast↔bread, fillet↔filet, nuts↔raw nuts,
   oats↔oatmeal, salad↔(dominant ingredient)`. Either hand-curated or
   learned from FDC food groupings.
2. **Word-order-invariant phrase matching** — today's contiguous-phrase
   bonus fires only for exact order; needs to fire for permutations.
3. **Processing-level preference** — a default tiebreaker toward
   less-processed / non-branded entries when the query is generic.
   USDA publication metadata doesn't make this easy; a learned feature
   or hand-tagged "is_canonical_generic" column on the taxonomy would.
4. **Composite-meal decomposition before retrieval** — the upstream
   narration parser has to emit per-ingredient food-strings, not
   meal-strings. Otherwise single-retrieval-per-meal is structurally
   wrong for the half of real queries that are composite.
5. **Brand-filtering for generic queries** — unless the user says a
   brand, demote branded entries.

Items (1), (3), and (5) are each plausibly 2–3 days of careful work.
Item (2) is a few hours. Item (4) belongs in the narration skill, not in
retrieval — but it must exist for meal-level retrieval to be coherent.

## Recommendation

The gate bucket is **<60% strict, <60% generous**. Per the plan's rule:

> <60%: defer meal-level; ship macros-only.

Concretely for Phase 5 scope:

- **Keep** the shipped `hai intake nutrition` daily-macros path as v1
  (7C.2). No retrieval required; it works today.
- **Drop** from Phase 5 scope: `hai intake meal`, `meal_log` raw table,
  `food_taxonomy` seeded from USDA, `skills/nutrition-intake/SKILL.md`,
  the meal-level branch of the projector, and all meal-log vs
  daily-macros precedence logic (Migration 006 simplifies accordingly).
- **Still in Phase 5 scope**: expanding `accepted_nutrition_state_daily`
  with micronutrient columns (useful even when null for macros-only),
  wiring `nutrition-alignment/SKILL.md` and classify/policy against the
  macros-only shape, X2 + X9 synthesis wiring against macros-only data.
  These do not depend on retrieval.
- **Defer to a point release** after v1 ships: USDA import, meal-level
  intake, narration skill, retrieval stack. When that work starts, the
  retrieval gate re-runs with the failure-mode fixes above and has to
  clear ≥80% before meal-level goes to users. Items (1)–(5) above give
  the re-run a fighting chance.

This recommendation shrinks Phase 5 from 3 weeks to roughly 1 week of
column-expansion + classify/policy work. The meal-level complexity that
was going to dominate Phase 5 moves to a later, narrower milestone with
its own retrieval re-gate.

## Caveats

- One session authored both the queries and the scorer. Bias check:
  the scorer was locked before queries were run (see commit history),
  but both were written by the same agent. A different agent scoring
  the same 20 queries would probably agree on the `miss` verdicts (they
  are categorically wrong) and might differ on `partial` vs `match`
  calls for q05/q12.
- Slice is 2018-vintage SR Legacy. Newer USDA data (Foundation Foods
  2025-12-18, ~1500 foods) has different naming conventions and might
  behave slightly differently — but not enough to move a <60% number
  above 60%. The failure modes are structural, not data-vintage.
- No evaluation of top-5 or top-10 accuracy. If Phase 5 uses a
  suggest+confirm UX, top-5 might be a more relevant metric — but that
  UX was already off the table at <60% top-1, per the plan's rules.
