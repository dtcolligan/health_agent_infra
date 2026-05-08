# Cycle artifact templates

Reusable scaffolds for per-cycle Codex audit prompts. Copy into
the cycle dir and customise — do not author from scratch.

## Files

- **`codex_plan_audit_prompt.template.md`** — D14 pre-cycle plan-
  audit prompt. Codex reviews `PLAN.md` for coherence before any
  code lands. Settled at the `10 → 5 → 3 → 0` 4-round signature
  for substantive PLANs.

- **`codex_implementation_review_prompt.template.md`** — IR post-
  implementation review prompt. Codex reviews the cycle branch diff
  + RELEASE_PROOF + REPORT. Settled at the `5 → 2 → 1-nit` 3-round
  signature for substantive cycles.

## Workflow

1. Copy the relevant template:
   ```bash
   cp reporting/plans/_templates/codex_plan_audit_prompt.template.md \
      reporting/plans/v0_1_X/codex_plan_audit_prompt.md
   ```

2. Customise these per-cycle sections only:
   - `> Why this round` framing — name the cycle's theme + scope.
   - `Step 1` orientation reading list — name this cycle's PLAN +
     any new strategic/tactical doc the cycle leans on.
   - `Step 2` audit questions — replace the per-W-id question
     stubs with this cycle's actual workstream catalogue.

3. **Do not modify** the stable steps:
   - Step 0 (confirm tree)
   - Step 3 (output shape)
   - Step 4 (verdict scale)
   - Step 5 (out of scope)
   - Step 6 (cycle pattern)
   - Step 7 (files this audit may modify)

   These are the universal contract — Codex relies on the same
   format every cycle.

4. Commit the prompt file as a cycle artifact (parallel to
   `PLAN.md`).

## Why templates

Empirically, the v0.1.11 + v0.1.12 audit chains relied on prompt
files that were ~90% identical across cycles. Re-authoring from
scratch each cycle wastes time and risks dropping a step. The
template approach codifies the stable surface; only the cycle-
specific scope changes.

Templates were extracted from the v0.1.12 cycle's working prompts
(`reporting/plans/v0_1_12/codex_plan_audit_prompt.md` +
`codex_implementation_review_prompt.md`).

## Adding new templates

If a future cycle introduces a new audit pattern (e.g., a
post-PyPI verification audit, a security-review prompt), add the
new template here with a parallel `*.template.md` filename and
update this README. Don't put one-shot prompts here — only patterns
that have been used at least twice.
