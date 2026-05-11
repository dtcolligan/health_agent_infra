# Predeclared Model Roster — Paper v1

**Status:** Pre-pilot artifact, drafted 2026-05-11 from
`framing_v2/CONVERGED.md` D-FRAME-020 (model roster) + D-FRAME-023
(cost ceiling).
**Pricing snapshot date:** 2026-05-11 (May 2026 pricing).
**Roster freeze status:** **Draft.** Maintainer must verify against
live vendor docs and freeze (compute SHA-256, record commit hash)
before any paper-claim model run.

This file is the canonical predeclared roster for the paper
"Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols" (NeurIPS 2027 main conference). Every paper-claim
trajectory/score artifact must reference this roster's SHA-256 hash
via the `model_roster_hash` field defined in
`schema/trajectory.schema.json` and `schema/score.schema.json`.

## Hash discipline

```bash
# Before any paper-claim run:
sha256sum benchmark/governed_agent_bench/model_roster.md
# Record the hash + the commit SHA in run logs.
# Update CONVERGED.md if the roster changes (new D-FRAME revision required).
```

## Roster (9 entries)

### Houdinis (6)

| # | Role | Model ID | Provider | Snapshot | Parameter count | Quantization | Decoding | Deprecation / replacement |
|---|---|---|---|---|---|---|---|---|
| H1 | Houdini (low) | `Qwen/Qwen2.5-3B-Instruct` | Hugging Face local (vLLM) | Freeze HF commit SHA at run time | ~3B | BF16 source weights for canonical run | `temperature=0`, `top_p=1`, max tokens per task family | Open weights; no provider retirement. If GGUF quantization used, record exact form (e.g. Q4_K_M) — do not mix with BF16 cells. |
| H2 | Houdini (mid) | `Qwen/Qwen2.5-7B-Instruct-Turbo` | Together AI | Provider snapshot on run date | ~7B | Vendor serving quantization undisclosed (`vendor_undisclosed_serving`); source weights BF16 | `temperature=0`, `top_p=1`, max tokens per task family | No public retirement found. Replacement: frozen HF `Qwen/Qwen2.5-7B-Instruct` self-hosted under new roster hash. |
| H3 | Houdini (mid+) | `accounts/fireworks/models/qwen2p5-32b-instruct` | Fireworks AI | Provider snapshot on run date | ~32B | Vendor serving quantization undisclosed; source weights BF16 | `temperature=0`, `top_p=1`, max tokens per task family | No public retirement found. Replacement: DeepInfra/Together/self-hosted Qwen2.5-32B under new roster hash. |
| H4 | Houdini (high open) | `accounts/fireworks/models/qwen2p5-72b-instruct` | Fireworks AI | Provider snapshot on run date | ~72B | Vendor serving quantization undisclosed; source weights BF16 | `temperature=0`, `top_p=1`, max tokens per task family | No public retirement found. Replacement: DeepInfra/Together/self-hosted Qwen2.5-72B under new roster hash. |
| H5 | Houdini (closed, low) | `claude-3-5-haiku-20241022` | Anthropic API | **Retired 2026-02-19** | Vendor undisclosed | Vendor undisclosed | `temperature=0`, fixed max tokens per task family | **RETIRED.** Usable only for already-collected D-FRAME-018 pilot trajectories. New cells must use `claude-haiku-4-5-20251001` under a new roster hash. |
| H6 | Houdini (frontier) | `claude-sonnet-4-20250514` | Anthropic API | Provider snapshot on run date | Vendor undisclosed | Vendor undisclosed | `temperature=0`, fixed max tokens per task family | **Retirement scheduled 2026-06-15.** §7.5 paper-claim cells must complete before that date OR re-anchor to `claude-sonnet-4-6` under a new roster hash. |

### Guards (3)

| # | Role | Model ID | Provider | Snapshot | Parameter count | Quantization | Decoding | Deprecation / replacement |
|---|---|---|---|---|---|---|---|---|
| G1 | Deterministic Guard (DRG-0) | `governed_agent_bench.drg.v0` (in-repo deterministic pipeline) | repo | Freeze scorer/guard config hash at run time | N/A | N/A | N/A — no sampling; thresholds frozen in committed JSON config | No provider risk. Replacement requires a new named deterministic guard config, not silent mutation. General Elo = 0 by definition (no LLM in decision path). |
| G2 | LLM Guard (calibration anchor) | `claude-3-5-haiku-20241022` | Anthropic API | Same as H5 | Vendor undisclosed | Vendor undisclosed | `temperature=0.2`, `top_p=1`, max 1,200 tokens, 5-vote majority | **RETIRED.** Same caveat as H5. Replace with Claude Haiku 4.5 successor for new cells. |
| G3 | LLM Guard (cross-vendor) | `gpt-4o-mini-2024-07-18` | OpenAI API | Provider snapshot on run date | Vendor undisclosed | Vendor undisclosed | `temperature=0.2`, `top_p=1`, max 1,200 tokens, 5-vote majority | No public retirement found. Replacement: current OpenAI mini model under new roster hash. |

## Coverage map

- **§7.1 trace-level evaluation:** 6 Houdinis × 2 primary runtime modes × 10 MVP tasks = 120 cells.
- **§7.2-7.4 mechanism ablations:** 4 representative Houdinis (H1, H2, H4, H6) × 5 single-mechanism-off modes × 10 MVP tasks = 200 cells.
- **§7.5 Engels Backdoor Code:** 6 Houdinis × 3 Guards × 225 APPS samples = 4,050 guard judgments. (Pilot subset: 60 samples × 3 Houdinis × 2 Guards = 360 judgments per D-FRAME-018.)
- **§7.6 Hierarchical Summarization bounded contrast:** 2 Houdinis × 3 monitors × L6 subset (per D-FRAME-024 bounded scope).

## Cost ceiling (D-FRAME-023)

USD 1,500 hard ceiling across all model API calls. Cells that cannot
fit within the ceiling are dropped, not silently absorbed.
Provider-substitution reruns triggered by Sonnet 4 retirement
re-anchor to `claude-sonnet-4-6` under a new roster hash.

## Pricing reference (snapshot 2026-05-11)

Verified during framing v2 round 4 audit (`framing_v2/round_4/AUDIT_RESPONSE.md`):

| Model | Input ($/MTok) | Output ($/MTok) | Source |
|---|---:|---:|---|
| Claude 3.5 Haiku (retired) | $0.80 | $4.00 | `platform.claude.com/docs/en/about-claude/pricing` |
| Claude Haiku 4.5 (current successor) | $1.00 | $5.00 | Same |
| Claude Sonnet 4 (retiring 2026-06-15) | $3.00 | $15.00 | Same |
| Qwen2.5-7B-Instruct-Turbo (Together) | $0.30 | $0.30 | `together.ai/pricing` |
| GPT-4o-mini (`2024-07-18`) | (verify) | (verify) | `platform.openai.com/docs/models` |

Maintainer: verify all rows against live vendor pricing pages
before computing the run-cost ceiling for the freeze.

## Freeze checklist (maintainer)

- [ ] Verify every model ID resolves on the named provider
- [ ] Verify pricing rows against live vendor docs as of run date
- [ ] Confirm Engels §4 "five Houdini attempts per sample" claim against arXiv:2504.18530 PDF (carry-over from F-AUDIT-3-05)
- [ ] Confirm Anthropic retirement dates current (Haiku 3.5 = retired; Sonnet 4 = 2026-06-15)
- [ ] Compute `sha256sum benchmark/governed_agent_bench/model_roster.md` and record in `framing_v2/ORCHESTRATOR_STATE.md` or a separate `roster_hash_log.md`
- [ ] Commit the frozen roster as a separate `git commit` so the commit SHA is the canonical roster reference
- [ ] Cite the commit SHA in `PROJECT_EXECUTION_PLAN.md` §7.X cell-allocation section
