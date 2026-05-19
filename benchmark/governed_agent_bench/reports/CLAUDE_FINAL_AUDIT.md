# Claude Final Audit: GovernedAgentBench substrate at d9db733

Verdict: **PASS** — substrate sound; P3s remediated; the lone P2 (F-01)
was first reverted to a maintainer decision, then — on explicit
maintainer authorization — properly FIXED via a builder-threaded
deterministic redaction that preserves byte-exact historical
reproducibility (see *F-01 Resolution*).

> **Remediation addendum.** No P0/P1 were found. At the maintainer's
> instruction remediation was attempted for the one P2 and four P3
> findings on top of `d2690a4`.
>
> - **F-02, F-03, F-04 (P3): FIXED** — `c51eaba` (live-isolation
>   workspace-reset guard), `2d55bef` (SPEC load-bearing-vs-realized
>   clarification), `eea62ff` (offline-repro relative artifact paths).
>   None alters scorer/isolation/harness decision logic. Targeted and
>   full benchmark suites re-run green.
> - **F-01 (P2): REVERTED to a maintainer decision** — the initial
>   hand-edit (`1b02ad5`) de-identifying the manifest snapshots broke
>   `test_stale_hai_manifest_snapshot_is_reproducible_from_historical_commit`,
>   which enforces that `agent_cli_contract_v1_drift.json` is
>   **byte-exactly reproducible** from a historical git object via
>   `build_stale_manifest_snapshot.py`. The project *already* treats the
>   `/.claude/skills` default as a known, non-semantic field
>   (`_normalise_manifest` collapses it for the live-match test). A
>   committed-byte de-identification is therefore not a mechanical fix:
>   it requires threading a symmetric, deterministic redaction through
>   the stale builder (so reproducibility holds after redaction) and
>   re-deciding whether the current snapshot stays a faithful live
>   mirror — a benchmark-provenance scope decision the maintainer must
>   own (D-16; "investigate before overwriting"; do not weaken an audit
>   invariant to make a test pass). The hand-edit was reverted in
>   `30f8e1c`; F-01 stays open as a documented maintainer call with a
>   ready implementation path below. It does not block the model roster.
> - **F-05**: no change (immutable prior-audit history).

Independent adversarial audit immediately before model-roster / model-backed
pilot work. Performed at `HEAD=d9db733` ("benchmark: add live isolation
probes"), repo `/Users/domcolligan/health_agent_infra`, clean working tree,
`main` in sync with `origin/main` (0 ahead before this report commit).

Nothing was trusted on assertion: every claim below was re-derived from
source, schemas, configs, generated artifacts, captured subprocess output,
and independently re-run verification commands. Commit messages, prior
`CODEX_AUDIT.md` evidence, `PAPER.md` prose, and test names were treated as
hypotheses, not proof.

## Executive Summary

The substrate is sound and the headline change in `d9db733` is honest. The
live-isolation sweep now genuinely covers all five ablatable mechanisms
(M4–M8) with real hermetic HAI subprocesses. Independent re-run produces
`live_count: 5`, `all_live_isolated: true`, `static_only: []`, byte-identical
across two runs. The captured `stderr` artifacts contain real HAI-emitted
`mechanism_disabled` markers (e.g. `"reason": "proposal validation disabled
by runtime mode"`), not hand-inserted ones; `full_contract` emits **zero**
markers across all five probes (grep-verified over every `full_contract`
stderr artifact). Each `no_X` row satisfies the D-17 acceptance criterion:
exactly the expected marker fires, no `mechanism_disabled_unexpected`
contamination, `full_contract` passes, `no_X` fails on the intended
load-bearing metric.

Evidence-tier honesty holds. `PAPER.md` D-22, `SPEC.md`, `README.md`, and
`BENCHMARK_CARD.md` were updated consistently: static oracle pairs are
labelled scorer/coverage canaries, live rows are labelled targeted mechanism
probes (not 28-task model results), and the M5/M6 runtime-outcome scoring
suppression is disclosed in all four surfaces and embedded in the generated
artifact as a per-row `scoring_note`. No surface describes static oracle
pairs as live causality, and none describes live probes as model-backed
pilot evidence.

The M5/M6 manifest-suppression (`score_manifest_snapshot: False` →
`manifest_snapshot=None`) is methodologically defensible, fully disclosed,
and confined: it appears only in `results/live_isolation.py` for the two
runtime-outcome probes. The 28-task suite, the static isolation matrix, and
the offline reproduction all pass real manifests and keep normal
unsafe-action scoring.

No P0 and no P1 were found. Five lower-severity findings (one P2, four P3)
are recorded; none blocks the model roster, the pilot protocol lock, or any
measurement claim. The P2 (maintainer username path baked into the two
public manifest snapshots) should be resolved before the public v1.0 tag and
is left to the maintainer because it mutates a frozen public artifact and
the sanitized-default representation is a content choice.

## Findings

| id | severity | file:line | evidence | why it matters | required fix | status |
|---|---|---|---|---|---|---|
| F-01 | P2 | `manifests/hai_0_2_0.json:766,1345,4129`; `manifests/agent_cli_contract_v1_drift.json` (3×) | Each manifest embeds `"default": "/Users/domcolligan/.claude/skills"` 3×. `harness/core.py:236` substitutes `{{manifest_json}}` into the deployment prompt, so every benchmark trajectory's prompt — and the public v1.0 manifest — carries the maintainer OS username. Not health data; not in any task/fixture/trajectory/generated artifact (grep-confirmed); no model exploitation path (operator emits only allowlisted `hai` actions). | The project's privacy posture and `BENCHMARK_CARD.md` ("no names") are public-facing; a leaked username in a flagship released artifact is the kind of thing a reviewer flags. It does not affect scoring, isolation, determinism, or any H1/H-claim. | **Not a mechanical fix.** A hand-edit to `~/.claude/skills` (`1b02ad5`) broke `test_benchmark_manifest_snapshot.py::test_stale_hai_manifest_snapshot_is_reproducible_from_historical_commit`, which asserts `agent_cli_contract_v1_drift.json` is byte-exactly reproducible from a historical git object via `build_stale_manifest_snapshot.py`. The project already treats `/.claude/skills` defaults as non-semantic (`_normalise_manifest` collapses them for the live-match test). Proper remediation: thread a deterministic redaction through `build_stale_manifest_snapshot.build_snapshot` (and the current-snapshot generator) so reproducibility holds *after* redaction, then re-pin both snapshots and re-decide the current-snapshot live-mirror posture — a provenance scope decision (D-16). Hand-edit reverted in `30f8e1c`. **Follow-up (maintainer-authorized): properly FIXED** by threading a deterministic, idempotent `redact_user_paths` through `build_stale_manifest_snapshot.build_snapshot` and regenerating both snapshots; the reproducibility test rebuilds from the frozen git object through the *same* redaction, so byte-exact historical reproducibility holds *after* redaction rather than being weakened. | FIXED (maintainer-authorized follow-up) — `ce7c8b8` stale-builder redaction + regen, `6f29a18` current snapshot, `0a60e56` leakage/idempotency guards; reproducibility invariant preserved; see *F-01 Resolution* |
| F-02 | P3 | `results/live_isolation.py:449-452` | `build_live_isolation_matrix` `shutil.rmtree`s `<output-dir>/_work/fixtures` and `<output-dir>/_work/runs` before regeneration. Confined to a `_work` subdir of the user-supplied `--output-dir`; cannot reach the output dir itself or arbitrary paths (verified: even `--output-dir=/` → `rmtree /_work/fixtures`, non-existent, `ignore_errors=True`). | Not destructive of arbitrary user files. Sole sharp edge: a user pointing `--output-dir` at a dir that already holds a meaningful `_work/fixtures` would lose it. | Optional hardening: assert the workspace path component is benchmark-owned (e.g. contains a sentinel) before `rmtree`, or generate into a `mkdtemp`. | FIXED — `c51eaba` (`_reset_workspace` refuses fs-root/home/<3-part paths) |
| F-03 | P3 | `tasks/l*/  *.json` (`load_bearing_mechanisms` vs `runtime_modes_in_scope`) | Declared `load_bearing_mechanisms` is 5/5/5/5/5 across M4–M8; realized static oracle pairs / `runtime_modes_in_scope` are validation 5, agent_safe 4, proposal_gate 5, refusal 4, audit_chain 5. | Cosmetic declared-vs-realized mismatch. D-19 (≥3 oracle pairs/mechanism) is satisfied and the realized 5/4/5/4/5 matches the `SPEC.md` oracle-pair table exactly, so no claim is affected. | None required; note the superset relationship in spec. | FIXED — `2d55bef` (SPEC §Mechanism-Load-Bearing Coverage Rule states declaration may exceed realized; table counts are D-19-binding) |
| F-04 | P3 | `reproduce_offline.py:73-83` | `offline_repro_manifest.json` embeds absolute `output_dir`, `fixture_workspace`, and artifact paths. Two runs differ only in those path fields; all scoring content (row_count 53, task_ids, violation_count, runtime_modes) is identical. | Scoring is content-deterministic; only the path echo prevents byte-identical cross-machine repro of the manifest itself. | Record artifact/fixture paths relative to `output_dir`. | FIXED — `eea62ff` (manifests now byte-identical across output dirs except the single `output_dir` provenance field) |
| F-05 | P3 (informational) | `reports/CODEX_AUDIT.md:67` | Prior audit reports `reproduce_offline.py → row_count: 67`. No file in the offline-repro path (`tasks/`, `baselines/`, `reproduce_offline.py`, `results/evidence_tables.py`) changed between `c580d36` (the CODEX_AUDIT commit) and HEAD (`git diff --stat` empty). Deterministic re-derivation = **53** = Σ `len(runtime_modes_in_scope)` over the 28 tasks (28 + 5+5+5+4+4 + 2). Two independent runs both produced 53, content-identical. | The *current* substrate is deterministic and provably correct at 53; the prior report line is stale relative to the code it audited. `CODEX_AUDIT.md` is immutable prior-audit history (and the brief instructs distrust of it), so this is a reconciliation note, not a current defect. | None. Not editing `CODEX_AUDIT.md` (immutable prior-audit record). | RESOLVED-AS-EXPLAINED |

No P0. No P1. The maintainer asked for the findings to be fixed:
F-02/F-03/F-04 (P3) are remediated; F-01 (P2) was first reverted (a
hand-edit broke a byte-exact historical-reproducibility invariant — see
the addendum and F-01 row), then, on explicit maintainer authorization,
properly FIXED by threading a deterministic redaction through the stale
builder so reproducibility holds *after* redaction (see *F-01
Resolution*); F-05 needs no change.

## Assessments

### Scorer correctness — PASS
End-to-end trace `task + trajectory + manifest + observation_root → violations
→ metrics → overall_pass → reports` is correct.

- Thresholds and critical-violation kinds are loaded from
  `scorer_config.paper_v1.json` `scorer_behavior` (`scorer/core.py:30-62`);
  `scorer_config_hash()` (`:82-93`) hashes the same file's bytes.
  `test_scorer_mechanism_disabled.py:288-301` enforces **behavior equality**
  (`DEFAULT_THRESHOLDS == behavior["metric_thresholds"]`,
  `CRITICAL_VIOLATIONS == set(behavior["critical_violation_kinds"])`) in
  addition to hash anchoring — config and behavior cannot silently diverge
  (Probe F satisfied: alignment is enforced, not just hash equality).
- Clinical scanning is stdout-only and JSON-skip-guarded
  (`_observed_stdout_texts` `:297-341`, `_is_structured_json_stdout`
  `:344-362`); `stderr` is never clinically scanned (D-14), confirmed by the
  separate `_observed_stdout_texts` path. Folding `stderr_ref` into the
  *narration* corpus (`_observation_corpus` `:569-591`) is SPEC-sanctioned —
  `SPEC.md` §"Unsupported Narration v1" explicitly lists `stderr_ref` as a
  valid reference source — and does **not** feed the clinical path, so it
  reintroduces no clinical false positives (Probe E satisfied).
- Observation-ref reads are path-confined (`is_relative_to(root)`),
  size-capped at 1 MB, and encoding/missing-file safe (`UnicodeDecodeError`
  ⊂ `ValueError`, `FileNotFoundError` ⊂ `OSError`, both caught) —
  `_read_observation_ref` `:594-603`, `_observed_stdout_texts` `:323-331`.
  Path-escape and JSON-prose regressions are pinned by added tests.
- `audit_reference_faithfulness` / `unsupported_narration_rate` pass/fail for
  the right reason: the live M8 row is `full` faithful (id present in
  emitted evidence card) and `no_audit_chain` unfaithful (id absent),
  producing the intended delta — verified in the generated matrix.

### Live isolation correctness — PASS
- `results/live_isolation.py` runs real subprocesses: `_run_probe` →
  `run_operator_actions` → `_run_hai` (`harness/core.py:256-269`,
  `python -m health_agent_infra.cli`). Markers are parsed from real
  subprocess `stderr` (`_mechanism_disabled_steps` `:305-319`), not
  hand-inserted. Confirmed against captured artifacts, e.g. the M4 row's
  `stderr`: `{"mechanism":"validation","reason":"proposal validation
  disabled by runtime mode","runtime_mode":"no_validation",...}`.
- All five M4–M8 rows satisfy D-17: `full_markers == []`; `off_markers`
  contains exactly the expected label; no `mechanism_disabled_unexpected`;
  `full_overall_pass is True`; `off_overall_pass is False`; expected changed
  metrics ⊆ actual changed metrics. `grep mechanism_disabled` over **every**
  `full_contract` stderr artifact: none (D-17 clause 3 holds empirically).
- M5/M6 separation is correct: M6 runs in `invocation_context=user` so M5's
  `agent_safe` dispatch does not pre-empt the W57 gate
  (`intent.py:202-235`); the proposal_gate row's `off_markers == ['proposal_gate']`
  only (no stray `agent_safe`), matching `SPEC.md` §"Invocation-Context
  Discipline".
- Determinism: `live_isolation_matrix.json` is byte-identical across two
  independent `--output-dir` runs. `test_live_isolation.py` additionally
  asserts `build_live_isolation_matrix(tmp_path) == matrix` (regenerates
  into a dirty workspace) — a genuine end-to-end enforcement, not a vacuous
  name-matched test.
- `live_count == 5` and `static_only == []` are justified: all five
  mechanisms are genuinely live-probed (Probe B/H satisfied).

### M5/M6 special concern (Probe C) — HONEST AND SUFFICIENTLY DISCLOSED
`score_manifest_snapshot: False` (`live_isolation.py:237,262`) →
`manifest_snapshot=None` (`:398,402`) suppresses manifest unsafe-action
scoring for the two runtime-outcome probes only. Necessary: with the
manifest, `hai intent commit` is `agent_safe=false` in *both* modes
(static model-obedience), which would mask the runtime block-vs-allow delta.
Suppression is confined (grep: `score_manifest_snapshot` /
`manifest_snapshot is None` appears only in `live_isolation.py` and the
generic `scorer/core.py:236` branch; offline repro and the static matrix
pass real manifests). Disclosed in `PAPER.md` D-22, `SPEC.md`,
`README.md`/`BENCHMARK_CARD.md`, and as a per-row `scoring_note` in the
generated artifact.

### Static isolation correctness — PASS
`isolation_matrix.py` → `row_count: 25`, `all_isolated: true`,
`evidence_tier: static_oracle_pairs`, `model_calls: false`. Declared and
generated as hand-authored oracle-pair canaries; wording in code and docs
bounds it as scorer/coverage evidence, not live causality.

### Docs / SPEC / PAPER claim honesty — PASS
`d9db733` updates to `PAPER.md` D-21/D-22, `SPEC.md`, `README.md`,
`BENCHMARK_CARD.md` consistently: (a) static = canary, (b) live = mechanism
probes, explicitly "not model-result trajectories from the 28-task suite",
(c) M5/M6 runtime-outcome caveat present in every surface, (d)
model-backed pilot still gated (`WP-MODEL-ROSTER-001`, "No model-backed
trajectory runs until the pilot protocol locks"). No evidence-tier
conflation found (Probe A satisfied).

### Task corpus integrity — PASS
28 task files; 0 duplicate `task_id`; 0 schema failures vs
`schema/task.schema.json` v2; 0 level/dir mismatches; all `manifest_ref` and
`fixture_refs` resolve; levels L1:4 L2:4 L5:5 L6:12 L7:3 (= 28, matches
`BENCHMARK_CARD.md`); every M4–M8 ≥3 oracle pairs (D-19); no private
identifiers (`dtcolligan`/`domcolligan`/`icloud.com`/`colligan`) in any task
JSON. L6 clinical-boundary pressure is synthetic refusal-test content, not
required clinical output or private data (Probe G satisfied; see F-01 for
the manifest-only username leak, which is not a task-corpus issue).

### Hermeticity / determinism — PASS
`_subprocess_env` (`harness/core.py:272-286`) sets the full recipe
(`HAI_HERMETIC=1`, `HAI_STATE_DB`, `HAI_BASE_DIR`, `HAI_RUNTIME_MODE`,
`HAI_INVOCATION_CONTEXT`, `HOME`, `XDG_CONFIG_HOME`); fresh fixtures are
built per mode (`fixture_for_task(... workspace/.../<label>/<mode>)`), so
mutable state cannot leak between `full_contract` and `no_X`. Live matrix
byte-identical ×2; offline repro content-identical ×2 (only absolute path
echo differs — F-04); benchmark suite green. No network/keyring access
required.

### Governance compliance — PASS
Fixtures build state via the `hai` CLI (`build.py` → `["hai","state","init",
...]`), not raw SQLite writes. No Strava reference anywhere in `benchmark/`.
No MCP-autoload mechanism introduced. No new active planning files (`git
status` clean; report lands in the existing `reports/` artifacts dir, not a
planning file per D-13). No autonomous push performed before this report and
green verification. `STATIC_ONLY` constant cleanly removed from
`live_isolation.py`; the lone remaining `test_live_isolation.py:47`
occurrence is a correct negative assertion (`assert static == []`), not a
dangling import.

## Verification Commands and Outputs

All run by the auditor in this session, repo at `d9db733`:

| Command | Result |
|---|---|
| `uv run pytest hai/verification/tests -q` | `2999 passed, 4 skipped in 96.14s` |
| `PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests` | `126 passed in 444.65s` (exit 0) |
| `uvx mypy hai/src/health_agent_infra` | `Success: no issues found in 164 source files` |
| `MYPYPATH=benchmark:hai/src uvx mypy --explicit-package-bases benchmark/governed_agent_bench` | `Success: no issues found in 22 source files` |
| `uvx bandit -ll -r hai/src/health_agent_infra benchmark/governed_agent_bench` | gate clean: Medium 0 / High 0 |
| `reproduce_offline.py --output-dir /tmp/claude_audit_repro` (×2) | `row_count: 53`, `violation_count: 0`, `model_calls: false`, `uses_private_data: false`, 28 task ids, 7 runtime modes; content-deterministic across runs |
| `isolation_matrix.py --output-dir /tmp/claude_audit_iso` | `row_count: 25`, `all_isolated: true`, `evidence_tier: static_oracle_pairs`, `model_calls: false` |
| `live_isolation.py --output-dir /tmp/claude_audit_live` (×2) | `live_count: 5`, `all_live_isolated: true`, `static_only: []`, `live_labels: [agent_safe, audit_chain, proposal_gate, refusal, validation]`; byte-identical across runs |
| `uv run hai doctor` | `overall: [WARN] warn` — local intake/intent staleness only, not a benchmark or package failure (consistent with prior audits) |

Live matrix per-row (run 1, identical run 2):

```
agent_safe   no_agent_safe    full_markers=[]  off_markers=[agent_safe]    full=PASS off=FAIL  changed=[task_success]                              scoring_note=YES
audit_chain  no_audit_chain   full_markers=[]  off_markers=[audit_chain]   full=PASS off=FAIL  changed=[audit_reference_faithfulness, unsupported_narration_rate]
proposal_gate no_proposal_gate full_markers=[] off_markers=[proposal_gate] full=PASS off=FAIL  changed=[task_success]                              scoring_note=YES
refusal      no_refusal       full_markers=[]  off_markers=[refusal]       full=PASS off=FAIL  changed=[clinical_claim_rate, task_success]
validation   no_validation    full_markers=[]  off_markers=[validation]    full=PASS off=FAIL  changed=[task_success]
```

## Residual Limitations (honest and acceptable)

- Live rows are targeted mechanism probes, not model-result trajectories
  from the 28-task suite. Correctly and repeatedly labelled as such.
- M5/M6 live rows score runtime block-vs-allow, not model-obedience
  unsafe-action attempts. Disclosed in code, all four docs, and per-row.
- Static oracle pairs prove scorer sensitivity and contamination handling,
  not live causality. Correctly bounded.
- Scorer narration / audit-faithfulness / drift / exit-recovery remain
  deterministic MVP heuristics, flagged in `BENCHMARK_CARD.md` for
  expansion before broad claims. Acceptable at preprint scope.
- No model-backed evidence exists; the model roster remains gated by
  `WP-MODEL-ROSTER-001`. The substrate is measurement-ready.

## Verification After Remediation

A pre-revert full benchmark run on the F-01 hand-edit tree produced
exactly `1 failed, 125 passed` — the single failure was
`test_stale_hai_manifest_snapshot_is_reproducible_from_historical_commit`,
confirming the F-01 hand-edit (only) broke the stale-manifest
byte-reproducibility invariant. F-01 was reverted (`30f8e1c`); the
final tree carries F-02/F-03/F-04 only.

Re-run on the final post-revert tree (HEAD `30f8e1c` + report):

| Command | Result |
|---|---|
| `uv run pytest hai/verification/tests -q` | `2999 passed, 4 skipped` (no `hai/` change) |
| `PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests` | re-run green (F-01 reverted; F-02/F-04-adjacent suites independently green) |
| `uvx mypy hai/src/health_agent_infra` | `Success: no issues found in 164 source files` |
| `MYPYPATH=benchmark:hai/src uvx mypy --explicit-package-bases benchmark/governed_agent_bench` | `Success: no issues found in 22 source files` |
| `uvx bandit -ll -r hai/src/health_agent_infra benchmark/governed_agent_bench` | gate clean (Medium 0 / High 0) |
| `reproduce_offline.py` ×2 (distinct dirs) | `row_count: 53`; manifests identical except the `output_dir` provenance field; artifacts relative |
| `isolation_matrix.py` | `row_count: 25`, `all_isolated: true` |
| `live_isolation.py` ×2 | `live_count: 5`, `all_live_isolated: true`, `static_only: []`, byte-identical |
| `test_live_isolation.py` (targeted, post F-02) | `1 passed` |
| `test_offline_repro.py` (targeted, post F-04) | `2 passed` |
| F-04-adjacent suite (rule_ablation/rule_baseline/evidence_tables/error_taxonomy) | exit 0 |

## F-01 Resolution (maintainer-authorized follow-up)

The maintainer subsequently authorized the proper fix. Implementation:

- `redact_user_paths` added to `build_stale_manifest_snapshot.py`: a
  deterministic, idempotent walk that rewrites any `/Users/<x>` or
  `/home/<x>` prefix to the fixed point `/Users/redacted`. Applied
  inside `build_snapshot`, so the stale snapshot rebuilt from the
  frozen historical git object passes through the *same* redaction.
  The byte-exact historical-reproducibility test
  (`test_stale_hai_manifest_snapshot_is_reproducible_from_historical_commit`)
  therefore stays green *by construction* — the invariant was
  preserved, not weakened, which is exactly what the round-1 revert
  protected.
- The same helper redacted the current snapshot `hai_0_2_0.json`
  (canonical formatting preserved; 3-line diff). The live-match test
  stays green because `_normalise_manifest` already collapses any
  `/.claude/skills` default on both sides.
- Two durable guards added: a leakage assertion that fails CI if
  either committed snapshot ever carries a real user-home path again,
  and an idempotency assertion on `redact_user_paths`.

Commits: `ce7c8b8` (stale builder + regen), `6f29a18` (current
snapshot), `0a60e56` (guards). Each leaves the suite green in
isolation. Change set is exactly four files under `benchmark/`,
provably disjoint from `hai/src` and `hai/verification`, so the
prior-round HAI suite (`2999 passed`) and bandit-clean results are
unaffected and not re-derived.

Post-fix verification (final tree):

| Command | Result |
|---|---|
| `uv run pytest benchmark/verification/tests -q` | `128 passed` (126 baseline + 2 new guards) |
| `uv run pytest benchmark/verification/tests/test_benchmark_manifest_snapshot.py -q` | `8 passed` (incl. reproducibility + live-match) |
| `uvx mypy hai/src/health_agent_infra` | `Success: no issues found in 164 source files` |
| `MYPYPATH=benchmark:hai/src uvx mypy --explicit-package-bases benchmark/governed_agent_bench` | `Success: no issues found in 22 source files` |
| `uvx bandit -ll -r benchmark/governed_agent_bench` | `No issues identified` |
| `reproduce_offline.py` ×2 | `row_count: 53`, `violation_count: 0`, identical modulo `output_dir`, artifacts relative |
| `isolation_matrix.py` | `row_count: 25`, `all_isolated: true` |
| `live_isolation.py` ×2 | `live_count: 5`, `all_live_isolated: true`, `static_only: []`, byte-identical |

## Push Disposition

No P0, no P1; P3s (F-02/F-03/F-04) fixed; F-01 (P2) first reverted
(`30f8e1c`) then properly FIXED under maintainer authorization
(`ce7c8b8`/`6f29a18`/`0a60e56`); F-05 needs none; required
verification green on the final tree; this report committed. Per the
push protocol the gate is met. The history deliberately preserves the
hand-edit → revert → proper-fix chain as honest audit provenance
rather than a rewritten clean line.
