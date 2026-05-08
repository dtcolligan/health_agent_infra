# Canonical checked-in artifacts root

This directory is the sole canonical checked-in proof root for the
repo.

## Active proof bundles

- ``flagship_loop_proof/2026-04-18-multi-domain-evals/`` — current.
  Full Phase 6 eval runner capture across all six v1 domains +
  synthesis. 28 scenarios, all green. Each scenario bundles frozen
  input, runtime result, and scored axes.

## Archived bundles

Pre-rebuild (single-domain / pre-reshape) bundles live under
``archive/``. They are retained for historical reference but do NOT
reflect the current multi-domain runtime contracts:

- ``archive/2026-04-16-recovery-readiness-v1/`` — pre-reshape Python
  flagship proof; the ``recovery_state`` objects in the captures
  reference types that no longer exist in ``schemas.py``.
- ``archive/2026-04-16-garmin-real-slice/`` — Garmin slice capture
  from before the Phase 7B training-readiness column rename and the
  Phase 3 sleep/stress migration.

Do not regenerate artifacts into the archive.

## Reviewer rule

- Use ``reporting/artifacts/`` for checked-in proof review.
- Keep new checked-in proof bundles under this root, dated, and
  named for the surface they prove.
- Do not recreate a repo-root ``artifacts/`` tree as a second live
  proof root.
