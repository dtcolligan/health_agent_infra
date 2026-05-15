# Maintainer Response — Codex Plan Audit round 1, v0.1.12 PLAN.md

**Author.** Claude (delegated by maintainer).
**Date.** 2026-04-29.
**Codex verdict.** `PLAN_COHERENT_WITH_REVISIONS`, round 1
(`reporting/plans/v0_1_12/codex_plan_audit_response.md`).

**This response.** Accepts 10 of 10 findings. Resolves 4 of 4 open
questions. PLAN.md revisions applied inline (this commit). The
revised PLAN goes back to Codex for round 2.

---

## Summary

Codex caught the right things. The strongest findings — F-PLAN-01
(CP5 contradicts §1.3), F-PLAN-03 (CP1/CP2 strike-text not
verbatim), F-PLAN-05 (CP6 deferred-and-required), and F-PLAN-06
(W-Vb premise asserted ModuleNotFoundError without reproducing
it) — are correctness bugs in the PLAN, not stylistic concerns.
F-PLAN-02 is the most embarrassing: I claimed three docs were
"confirmed on disk 2026-04-29" but two of them had already been
fixed during the same-day reorg. Codex did the on-disk
verification I should have done.

The provenance gaps (F-PLAN-02, F-PLAN-06, F-PLAN-09) all trace
to the reconciliation document's §8 self-flag that 4/8 round-2
research agents failed. Codex's Q8 framing was the right
counterweight — independent on-disk verification of un-verified
primary sources. Will internalise: when authoring a PLAN that
leans on a synthesis document, treat the synthesis as input that
needs spot-verification, not as ground truth.

---

## Per-finding dispositions

| F-id | Disposition | PLAN.md revision |
|---|---|---|
| **F-PLAN-01** (CP5 sequencing) | accepted | §1.3 deferral table reframes to single substantial v0.2.0 (W52 + W53 + W58 deterministic-block + LLM judge shadow-by-default with feature flag); v0.2.1/v0.2.2 split removed; CP5 row in §2.10 aligned. |
| **F-PLAN-02** (W-AC / W-PRIV provenance) | accepted | §2.1 drops `HYPOTHESES.md` + `reporting/plans/README.md` from "confirmed on disk" list (already fixed during 2026-04-29 reorg per Codex spot-verify). §2.7 drops chmod paragraph (already documented at `privacy.md:44-46`). |
| **F-PLAN-03** (CP1/CP2 strike-text) | accepted | §2.10 quotes AGENTS.md verbatim ("**W-29 / W-30 deferred.** Do not split `cli.py`. Do not freeze the capabilities manifest schema yet.") + the Do Not Do bullet. CP1 and CP2 framed as paired changes to the joint settled-decision bullet. |
| **F-PLAN-04** (W-CP approval) | accepted | §2.10 adds per-CP acceptance gate with `accepted / accepted-with-revisions / rejected` states + target files + delta blocks + rejection fallback. "Implicit-approval" language removed. |
| **F-PLAN-05** (CP6 split state) | accepted | CP6 authored as proposal in v0.1.12; §6.3 edit applied at v0.1.13 strategic-plan rev (matches existing §1.3 deferral row). §3 ship gates and §5 DoD updated to require CP1-CP5 deltas only at v0.1.12 ship; CP6 application deferred. |
| **F-PLAN-06** (W-Vb premise) | accepted | §2.3 rewritten. Current state described as "persona slug accepted but no fixture loading mechanism exists" with file:line citations from Codex. ModuleNotFoundError claim removed. Two coupled deliveries reframed: (a) packaged-fixture path + loader, (b) loading wired into `open_session()`. |
| **F-PLAN-07** (W-FBC option B) | accepted | §2.8 reframes as design-first. Acceptance: policy decision documented (recovery picked as one-domain prototype) + named persona scenarios (P1/P5/P9) + `--re-propose-all` override. Multi-domain rollout deferred to v0.1.13 W-FBC-2 if required. |
| **F-PLAN-08** (W-N split fallback) | accepted | §2.5 replaces in-suite recursive test with CI subprocess command-gate + a small smoke test. Adds 3-step fallback ladder (≤80 / 80-150 / >150 sites). |
| **F-PLAN-09** (W-DOMAIN-SYNC scope) | accepted | §1.3 deferral row reframed to "single truth table + expected-subset assertions; not all 8 named tables are six-domain registries (Codex F-PLAN-09)." |
| **F-PLAN-10** (Phase 0 unscoped) | accepted | New §6 Phase 0 outline added: probes, expected artifact, cycle-impact tags, abort/revise triggers per workstream. |

---

## Open question resolutions

### Q1 — CP5 D1 adjudication

**Resolution: single substantial v0.2.0** (W52 + W53 + W58
deterministic claim-block + W58 LLM judge shadow-by-default with
feature flag to flip to blocking).

The maintainer's 2026-04-29 chat call was "v0.2.0 to be pretty
substantial, we can always fix bugs in future" + on the LLM judge
specifically: "we should be more cautious on the LLM judge in
blocking mode." Synthesis: the LLM-judge caution is internalised
as a feature flag (`HAI_W58_JUDGE_MODE = shadow | blocking`)
within v0.2.0, not a release boundary. Flip to blocking happens
inside v0.2.0 (or v0.2.0.x) once shadow-mode evidence supports
it.

The reconciliation's three-release synthesis was the
recommendation under the assumption that the maintainer would
prefer staging. Maintainer override toward "more substantial"
collapses staging into the feature-flag semantics within one
release.

### Q2 — CP3 fallback if revised/rejected

**Resolution.**
- If CP3 `accepted-with-revisions` → v0.1.12 declares its tier
  per the revised D15 wording.
- If CP3 `rejected` → v0.1.12 declares no tier; D11/D14 audit
  weight follows pre-v0.1.12 norm.

Encoded in CP3's per-CP acceptance gate in §2.10.

### Q3 — W-PRIV: ship `hai auth --remove`?

**Resolution: ship the command.**

Codex F-PLAN-02 / verified during audit confirmed
`clear_garmin()` and `clear_intervals_icu()` helpers already
exist in `core/credentials.py`. CLI surfacing is the missing
piece (~half day). Cheaper than maintaining a doc-says-no-such-
command discrepancy. PLAN §2.7 commits to (A) ship.

### Q4 — CP4 least-privilege threat model

**Resolution: add explicit security/threat-model gate to CP4
acceptance.** No MCP read surface ships before:

- Least-privilege read-scope model documented.
- Threat-model artifact at `reporting/docs/mcp_threat_model.md`
  naming resource audience validation, confused-deputy risk,
  token-passthrough risk, SSRF risk, with stated mitigations for
  each.
- Provenance contract verified through one full domain.

Sources cited in CP4 proposal doc:
- <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
- <https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices>

Codex's MCP-spec citation is taken at face value here; the
threat-model doc itself will need to verify the spec language at
authoring time (v0.4 prereqs).

---

## CP1-CP6 quick-verdict response (matches Codex's table)

| CP | Codex verdict | Disposition | Action |
|---|---|---|---|
| CP1 | revise | accepted | Revised in §2.10: AGENTS.md verbatim quote + paired-change framing with CP2. |
| CP2 | revise | accepted | Revised in §2.10: paired with CP1; downstream contract implications listed. |
| CP3 | accept-with-revision | accepted | Per-CP fallback added (§2.10 + Q2 above). |
| CP4 | accept-with-revision | accepted | Security/threat-model gate added (§2.10 + Q4 above). |
| CP5 | revise | accepted | Reframed as single substantial v0.2.0 with shadow-by-default flag (§2.10 + §1.3 + Q1 above). |
| CP6 | revise | accepted | Author-now / apply-at-v0.1.13 split made explicit (§2.10 + F-PLAN-05). |

---

## Verified during this response

- AGENTS.md current text for "Settled Decisions" W-29/W-30
  bullet and "Do Not Do" cli.py/manifest bullet quoted verbatim
  in revised §2.10.
- v0.1.11 RELEASE_PROOF §5 carry-overs cross-checked: every line
  has a disposition row in W-CARRY scope.
- Reconciliation §3 D1 reasoning re-read; revised CP5 framing
  matches maintainer 2026-04-29 chat call (substantial v0.2.0;
  shadow-by-default refinement on LLM judge).
- Codex F-PLAN-06 file:line citations (`cli.py:8530-8537`,
  `core/demo/session.py:226-230`, `pyproject.toml:53-62`) taken
  at face value for §2.3 rewrite; spot-verify at workstream
  start.

---

## Out of scope for this response

- No code changes (Phase 0 hasn't started; no implementation
  yet).
- No test runs (D14 audit prompt Step 7 explicitly forbids).
- No application of CP1-CP5 deltas to AGENTS.md / strategic plan
  / tactical plan — those apply at v0.1.12 ship per CP acceptance
  gates, not at PLAN-revision time.

---

## Round-2 expectation

The PLAN.md revisions in this commit address every Codex finding
and resolve every open question. Round 2 should be either:

- `PLAN_COHERENT` (if revisions are clean) → cycle opens.
- `PLAN_COHERENT_WITH_REVISIONS` (if any revision introduces a
  second-order issue) → another round, addressing only the new
  findings.

The v0.1.11 empirical norm was 4 rounds. v0.1.12's first round
surfaced 10 findings — comparable to v0.1.11's 10. If the
revisions in this commit resolve cleanly, we may settle in 2-3
rounds rather than 4.
