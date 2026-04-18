# Archived doctrine docs (pre-rebuild)

These documents describe the pre-rebuild single-domain system — the
recovery-readiness flagship loop as it stood on 2026-04-17. They are
preserved here for historical context but are NOT authoritative for
the current v1 multi-domain runtime.

Every claim below is superseded by the current docs at
``reporting/docs/``:

| Archived doc | Superseded by |
|---|---|
| ``canonical_doctrine.md`` | ``architecture.md`` + ``non_goals.md`` |
| ``chief_operational_brief_2026-04-16.md`` | ``architecture.md`` |
| ``founder_doctrine_2026-04-17.md`` | ``architecture.md`` + ``non_goals.md`` |
| ``phase_timeline.md`` | Git log (``git log --oneline``) is the authoritative timeline for the rebuild |

Specifically note:

- The "five skills" framing (recovery-readiness, reporting,
  merge-human-inputs, writeback-protocol, safety) is obsolete. v1
  ships twelve skills spanning six domains, a synthesis skill, plus
  the pre-rebuild cross-cutting skills.
- The "runtime holds no classification" framing is obsolete. v1
  moves classification + mechanical policy into code (per-domain
  ``classify.py`` + ``policy.py``), keeping only judgment in skills.
- The "single TrainingRecommendation contract" framing is obsolete.
  v1 has per-domain proposal + recommendation schemas plus a
  synthesis layer that reconciles them into a daily_plan.

Do not cite these docs as current truth. If a reader lands here
expecting an overview, redirect them to ``reporting/docs/README.md``
or the top-level ``README.md``.
