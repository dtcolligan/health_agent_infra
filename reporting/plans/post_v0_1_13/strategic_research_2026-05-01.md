# Strategic Research — Post v0.1.13 (2026-05-01)

Operational research input for v0.1.14 PLAN.md, cycle proposals, risk-register
updates, and v0.1.14 / v0.2.0 / v0.3+ roadmap decisions. v0.1.13 shipped
2026-04-30 (substantive tier, 17 W-ids, D14 5-round 11→7→3→1-nit→0, IR
3-round 6→2→0, SHIP).

Author: research session adopting Codex-equivalent adversarial-review posture
per project's external-audit conventions. Method, evidence ledger, and
external citations live in §3 and §21. Recommendations are blunt by design.

---

## 1. Executive Verdict

**The current v0.1.x cadence is operating well; the strategic plan is
internally coherent; the published April-2026 wearable-agent literature
validates HAI's core bets more cleanly than at any prior cycle close. There
are also five things that will silently break trust the moment a second user
opens this repo, and the current v0.1.14 / v0.2.0 scope does not address
any of them.**

> **Round-1 Codex audit applied 2026-05-01.** Codex returned
> REPORT_SOUND_WITH_REVISIONS with 10 findings; 9 accepted, 1 partial-
> accept (F-RES-03 / C6 vs CP5). Revisions in place across §1, §2, §3,
> §5, §6, §10, §11, §13, §14, §15, §18, §19, §20, §21, §22. See
> `codex_research_audit_round_1_response.md` for the per-finding
> disposition.

Verdict by question:

1. **What would make this fail despite the roadmap shipping?**
   Second-user supportability, source-row provenance, MCP threat-model
   discipline, and `hai explain` confusion-vs-clarity validation. None
   are scoped today.
2. **What's hidden by N=1 dogfood?**
   Onboarding empirical proof (the test surface ships, the empirical
   proof does not). Foreign-machine recovery paths (`hai backup` /
   `hai restore` / `hai export` are absent). Persona archetypes that
   stress *trust-formation*, not just classifier coverage.
3. **What's miss-scoped right now?**
   v0.1.14's tactical-plan baseline (W-AH/W-AI/W-AJ/W-AL/W-AM/W-AN +
   inherited W-29/W-Vb-3/W-DOMAIN-SYNC, ~9 W-ids, 15-22 days) is
   *under-counted* in the report's earlier draft. With the 5 P0
   additions surfaced here, v0.1.14 grows to ~14 W-ids / 32-45 days
   (revised from initial 30-40 estimate per v0.1.14 D14
   F-PLAN-R2-01 + F-PLAN-R3-01 sizing-propagation closures).
   v0.2.0 carries weekly review + insight ledger + judge shadow + W-30
   schema freeze in one cycle — CP5 settled "single substantial
   release" on W52↔W58 design-coupling grounds, but the reconciliation
   *also* settled C6 ("one conceptual schema group per release"), and
   CP5 did not engage with C6. The two constraints are in tension; the
   maintainer must choose between Path A (3-release split per
   reconciliation D1, honoring C6) and Path B (single-release per CP5
   with a new CP overriding C6). The report recommends Path A.
4. **What should v0.1.14 do first?**
   Land the **second-user gate** (W-2U-GATE) and **source-row
   provenance type** (W-PROV-1) before W52 design begins.
5. **What should split out of v0.2.0?**
   W-30 capabilities-manifest schema freeze (move to a v0.2.0.x or
   v0.2.1 hardening tier). If Path A is chosen for the v0.2.0 split,
   W53 + W58-judge-shadow also move to v0.2.1 to satisfy C6.
6. **What needs more evidence before shipping?**
   MCP exposure (defer past v0.4 until a published threat-model
   artifact + 2026 CVE-class review lands). LLM-judge promotion to
   blocking (defer until shadow-mode evidence is published, not
   merely accumulated).
7. **What should never ship without reopening a settled decision?**
   Hosted relay, Strava-anchored pull, autoload-from-repo MCP
   install, autonomous training-plan synthesis, threshold mutation
   without explicit user commit, multi-tenant deployment.

The project is on a good trajectory. The risks are concentrated in
*supportability* and *MCP exposure*, not in the core runtime. Address
those as P0 in v0.1.14 and the v0.2.0 substrate work has a much higher
ship-on-time probability.

---

## 2. Research Method

Six staged phases, executed concurrently where independent:

1. **Phase 1 — Repo evidence ledger.** Direct read / grep of 29 canonical
   files (AGENTS, README, ARCHITECTURE, REPO_MAP, ROADMAP, AUDIT,
   CHANGELOG, HYPOTHESES, all reporting/docs/, all reporting/plans/,
   v0.1.13 cycle artifacts, dogfood README, capabilities tests). Output:
   ledger with file:line citations.
2. **Phase 2 — Contradiction hunt.** Cross-doc drift audit, plus a
   second ROADMAP.md pass to catch narrative/dependency-chain drift.
3. **Phase 3 — Roadmap stress test.** Direct read of strategic_plan_v1,
   tactical_plan_v0_1_x, reconciliation, RELEASE_PROOF v0.1.13.
4. **Phase 4 — External landscape.** Web research on wearable MCPs,
   self-hosted PHRs, commercial coach surfaces, MCP security state-of-
   art, regulatory regime. Primary sources where available; vendor
   statements, trade press, and security advisories used for landscape
   claims and explicitly flagged in §21 with a source-class label.
5. **Phase 5 — Research literature.** PHA / PHIA / PH-LLM / SePA /
   AgentSpec / FActScore / MedHallu / JITAI meta-analysis / StudyU /
   LLM-as-judge bias literature / MCP CVE catalogue / wearable-privacy
   literature.
6. **Phase 6 — Adversarial reviews.** Seven reviewer lenses (product
   skeptic, maintainer-load skeptic, security skeptic, research
   skeptic, governance skeptic, user-support skeptic, roadmap
   skeptic) applied to synthesis.

Provenance discipline: every claim in §5–§20 traces either to a cited
file:line in the repo or to an external source listed in §21, with
source class noted where material; explicit per-citation source-class
labels (paper / spec / vendor statement / trade press / security
advisory / product documentation) are deferred to a v0.1.14 doc-fix
sweep (W-FRESH-EXT). Where I extrapolate from abstract-level reading
rather than full-text, I flag it. Where I disagree with the strategic
plan or reconciliation, I name the disagreement and what would change
my mind.

---

## 3. Evidence Ledger Summary

**Project state at v0.1.13 ship (2026-04-30):**

| Surface | Value | Source |
|---|---|---|
| Package version | 0.1.13 | pyproject.toml:7 |
| Migrations | 22 (001..022) | src/health_agent_infra/core/state/migrations/ |
| Skills shipped | **14** (README claims 15 — drift) | skills/ ls; README.md:48 |
| Tests passing | 2493 (+109 vs v0.1.12) | RELEASE_PROOF.md:69-71 |
| Mypy errors | 0 (held; 120 source files) | RELEASE_PROOF.md:94-100 |
| Bandit Low | 46 (held; 0 Med/High) | RELEASE_PROOF.md:104-108 |
| Broader-warning gate | clean (was 49 fail + 1 error) | RELEASE_PROOF.md:79-89 |
| CLI commands | 56 | RELEASE_PROOF.md:128-133 |
| Personas in matrix | 12 (P1..P12) | personas/__init__.py:34-37 |
| cli.py size | 9217 lines | wc -l (D4 trip-wire is 10000) |
| synthesis.py size | 1177 lines | wc -l |
| Settled decisions | D1..D15 | AGENTS.md:112-211 |
| Hypotheses | H1..H5 (all active) | HYPOTHESES.md, strategic_plan_v1.md §3-§5 |

**Roadmap state:**

- **v0.1.14 (in flight, target 2026-Q3):** **9-W-id baseline** per
  tactical_plan_v0_1_x.md:394-409 — W-AH (scenario expansion),
  W-AI (ground-truth methodology), W-AJ (LLM-judge harness scaffold),
  W-AL (calibration eval), W-AM (adversarial fixtures), W-AN
  (`hai eval run --scenario-set` CLI) + inherited W-29 (cli.py split),
  W-Vb-3 (9-persona residual), W-DOMAIN-SYNC. Tactical-plan effort:
  15-22 days. ROADMAP.md:36-43.
- **v0.2.0 (target post-v0.1.14 + 2-4 weeks → Q3 late / Q4 2026):** W52
  weekly review + source-row locators, W53 insight ledger, W58
  deterministic claim-block (blocking from day 1), W58 LLM judge ships
  shadow-by-default with `HAI_W58_JUDGE_MODE` flag, W-30 capabilities-
  manifest schema freeze last. **CP5 settled "single substantial
  release" on W52↔W58 design-coupling grounds**
  (tactical_plan_v0_1_x.md:441-501); reconciliation C6 separately
  settled "one conceptual schema group per release"
  (reconciliation.md:147). The two constraints are in tension; §11
  names the choice. ROADMAP.md:44-49.
- **v0.3+ (MCP staging):** v0.3 plans MCP server (read-surface design +
  threat-model + provenance contract); v0.4 prereqs (least-privilege
  scope + threat-model completion); v0.4-or-v0.5 ships MCP read.
  No write surface ever. ROADMAP.md:50-53.
- **v0.5+ → v1.0:** N-of-1 substrate → personal-evidence estimator
  (v0.6) → governed adaptation (v0.7) → ≥3 months zero-incident → v1.0.

**Five hypotheses, all active, none falsified at v0.1.13:**

- H1 — interpretability > better recommendations.
- H2 — local-first beats hosted.
- H3 — user intent/targets + bounded supersession is the right substrate.
- H4 — LLM driving deterministic CLIs > end-to-end reasoning.
- H5 — small governed ledgers + strict code-vs-skill > multi-agent prose.

Validation status: H1/H3/H4/H5 each carry one v0.1.10 N=1 confirmation.
H2 has no recent update beyond local-LLM-hardware non-regression.

**Key external anchors (April 2026):**

- **Google PHA** (arXiv 2508.20148, Aug 2025): three-sub-agent framework,
  largest published budget. Direct competitor architecture.
- **PHIA** (Nat Commun 2026): tool-using agentic reasoning beats
  non-agentic numerical/code-generation baselines on wearable-data
  questions. Validates H4's "agent drives deterministic tools" half.
- **AgentSpec** (arXiv 2503.18666, ICSE '26): the literature now has
  vocabulary for HAI's skill-vs-code invariant.
- **MedHallu** (arXiv 2502.14302): "not sure" abstention category boosts
  F1 by up to 38%; GPT-4o caps F1=0.625 on hard medical hallucinations.
- **JITAI 2025 meta-analysis** (PMC12481328): g=0.15 — recommendations
  are a small lever; H1 anchored, but "outcome improvement from
  coaching" is no longer defensibly citable.
- **Strava Nov 2024 ToS update**: AI/ML use of Strava data prohibited;
  intervals.icu was specifically named.
- **Apple App Store medical-device-status disclosure policy (effective
  by 2027)**: platform-level compliance signal that health apps must
  declare medical-device status. Source-class: trade press (MDDI), not
  a regulator-issued mandate. (Original draft over-framed this as a
  regulatory action; corrected per Codex F-RES-08.)
- **OWASP MCP Top 10 (2026 beta)**: HAI's existing invariants map
  cleanly to it.
- **CVE-2025-59536 / CVE-2026-21852** (Check Point): malicious project
  files trigger MCP autoload + ANTHROPIC_BASE_URL hijack →
  exfiltrate Anthropic API keys. **Material to HAI because HAI runs
  inside Claude Code.**
- **CVE-2025-6514, 53109, 53110** plus **OX Security's April 2026 MCP
  STDIO disclosure**: command-injection / path-traversal risk is not
  hypothetical in MCP servers. I did not verify the previously circulated
  22% / 43% aggregate figures, so this report does **not** rely on them.

### Required Evidence Ledger

| Claim | Source file/link | Evidence | Confidence | Implication | Follow-up question |
|---|---|---|---|---|---|
| HAI's core contract is CLI-mediated local governance, not an AI coach. | `AGENTS.md:8-12`, `README.md:3-5`, `README.md:24`, `reporting/docs/agent_cli_contract.md:58-112` | Project description, local SQLite commit path, and 56-command manifest surface all point to `hai` as the agent contract. | High | Do not build hosted UI, raw DB write paths, or MCP write surfaces. | Should README name "runtime enforcement" more explicitly now that AgentSpec exists? |
| The code-vs-skill boundary is a load-bearing invariant. | `AGENTS.md:52`, `reporting/docs/architecture.md:115-144`, `reporting/docs/agent_integration.md:119-150` | Skills own judgment/prose; Python owns deterministic state, validation, and writeback. | High | W58 and W52 must be code-owned for factuality and provenance; prose only renders already-computed facts. | Should skill-lint assert "no band/rule computation" text patterns? |
| Current roadmap correctly prioritizes v0.1.14 eval substrate and `cli.py` split, but omits second-user proof. | `ROADMAP.md:31-43`, `reporting/plans/tactical_plan_v0_1_x.md:384-436`, `reporting/plans/v0_1_13/RELEASE_PROOF.md:46` | v0.1.14 is eval + W-29 + W-Vb-3; W-29-prep is green. No artifact proves a non-maintainer clean install. | High | Add W-2U-GATE before W52/W58 design work. | Who is the first external tester and what machine/env will they use? |
| v0.2.0 is over-concentrated if W52, W53, W58D, W58J, and W-30 all remain in one release. | `ROADMAP.md:44-49`, `reporting/plans/tactical_plan_v0_1_x.md:450-490`, `reporting/plans/future_strategy_2026-04-29/reconciliation.md:54-80` | Tactical plan keeps a single substantial release; reconciliation had already argued for deterministic-first split. | High | Split W-30 out; consider W58J blocking only after shadow evidence. | Is there a schema-coupling reason W-30 cannot move to v0.2.0.x? |
| Source-row locators are prerequisite, not polish, for deterministic factuality. | `reporting/plans/future_strategy_2026-04-29/reconciliation.md:146-151`, `reporting/plans/tactical_plan_v0_1_x.md:461-463` | Reconciliation names source-row locators for every quantitative claim; W58D blocks unsupported claims from day 1. | High | Add W-PROV-1 in v0.1.14, before weekly-review implementation. | Can existing `derived_from` accepted-state fields carry enough row/column/version detail? |
| Outcome / calibration substrate is explicitly not built. | `reporting/plans/eval_strategy/v1.md:65`, `reporting/plans/eval_strategy/v1.md:125-129`, `reporting/plans/eval_strategy/v1.md:365-395` | Eval strategy says calibration requires v0.2 weekly review + insight ledger; defines later confidence/outcome correlation. | High | W-AL should stay schema/report-only in v0.1.14 and not claim real calibration. | What minimal schema avoids rework when W58 atomic claims arrive? |
| Persona harness still misses trust-formation and low-domain-knowledge UX. | `verification/dogfood/README.md:4-14`, `verification/dogfood/README.md:52-77`, `verification/dogfood/personas/__init__.py:34-37` | 12 synthetic user shapes exercise domain axes, not "can a second user understand `hai explain`?" | High | Add P13 or a manual explain-UX review before v0.2.0. | Should P13 be a real non-maintainer transcript or a synthetic persona first? |
| Rationale/prose eval remains deliberately skipped in deterministic eval rubrics. | `src/health_agent_infra/evals/rubrics/domain.md:45-50`, `src/health_agent_infra/evals/rubrics/synthesis.md:51-57`, `reporting/plans/eval_strategy/v1.md:176-178` | Rubrics mark rationale quality as `skipped_requires_agent_harness`. | High | W58 cannot be only a model-judge layer; deterministic factuality must precede it. | Should v0.1.14 add a skill-harness smoke, or leave it to W58? |
| README has a stale skill count. | `README.md:48`; `find src/health_agent_infra/skills -mindepth 1 -maxdepth 1 -type d | wc -l` | README says 15 skills; repo has 14 skill directories. | High | Fix as a doc-only freshness item. | Can doc freshness tests count packaged skills mechanically? |
| ROADMAP dependency chain contains stale historical content. | `ROADMAP.md:80-83`, `CHANGELOG.md:14-21`, `reporting/plans/tactical_plan_v0_1_x.md:441-501` | ROADMAP still names v0.1.9 weekly review / v0.2 BCTO / v0.3 first-run UX, but current plan has W52 at v0.2.0 and first-run UX shipped in v0.1.13. | High | Fix ROADMAP before PLAN.md inherits wrong dependencies. | Should narrative dependency chains be tested for forbidden historical W-ids? |
| Backup/export exists as manual file-copy guidance, not governed CLI. | `reporting/docs/privacy.md:93-99`, `reporting/docs/privacy.md:134-139`; no `add_parser("backup"|"restore"|"export")` in `cli.py` | Privacy doc tells users to copy `state.db`; CLI lacks first-class backup/restore/export/support commands. | High | Second-user readiness needs W-BACKUP. | Should backup include credentials metadata, or explicitly exclude secrets? |
| No clinical/provider/hosted/nutrition expansion should be recommended. | `reporting/docs/non_goals.md:10-15`, `reporting/docs/non_goals.md:49-62`, `reporting/docs/non_goals.md:90-95`, `AGENTS.md:386-397` | Non-goals forbid clinical claims, EHR/provider integration, hosted product, meal-level nutrition, and autonomous plans. | High | Tempting features from Fasten/HealthLog/Gyroscope are out-of-scope unless decisions reopen. | Should AGENTS.md add "No Strava AI path" explicitly? |
| Current test and migration surfaces are large enough that W-29 split is urgent but controllable. | `src/health_agent_infra/cli.py` 9217 lines, 22 SQL migrations, 177 `test_*.py` files, `verification/tests/test_cli_parser_capabilities_regression.py:1-17` | The CLI is under the 10k trip-wire but already guarded by manifest/parser snapshots. | High | Split before W52/W53 add commands; preserve byte-stable capabilities. | What exact module boundaries minimize import churn? |
| PHIA supports tool-mediated wearable reasoning, but also shows numeric provenance matters. | Nature Communications PHIA, lines 70-73, 146-163 | PHIA achieves 84% objective accuracy and reduces code errors, but the task is explicit data reasoning with tools. | High | HAI's H4 holds; source-row and deterministic checks are the local-first equivalent. | Which PHIA query categories map to W52 weekly review claims? |
| JITAI/EMI literature argues against overclaiming coaching benefit. | BMJ Mental Health JITAI meta-analysis, 2025, `g=0.15` in abstract. | Small pooled effect; risk of bias around adherence/missing data. | Medium-high | Keep H1 framed as interpretability/trust, not "AI coaching improves outcomes." | Should success metrics down-weight recommendation-following and up-weight explainability use? |
| LLM judges are useful only behind deterministic references and shadow evidence. | FActScore, MedHallu, No Free Labels, Rating Roulette, MCP spec/OWASP sources in appendix | Atomic-fact support, abstention, reference answers, and intra-rater stability are all known issues. | High | W58J must ship shadow-by-default with bias/stability panels; blocking needs evidence. | What bias thresholds are required before flag flip? |

### External Landscape Findings

| Surface | Evidence | Extracted lesson for HAI |
|---|---|---|
| Garmin / Oura / WHOOP / Intervals.icu MCPs | Community MCP servers already expose activities, sleep, readiness, recovery, strain, wellness, and event data via local or hosted MCP servers. Intervals.icu has a GPL MCP server; Oura MCPs advertise OAuth/PKCE and token encryption; Garmin MCPs often depend on `python-garminconnect`. | Data access is becoming commodity. HAI should not chase breadth; it should win on governance, provenance, explainability, and refusal. |
| Apple Health via Open Wearables | Open Wearables documents Apple HealthKit SDK sync, provider normalization, self-hosted deployment, and an MCP server / AI reasoning layer. | Normalized wearable ingestion may be better consumed upstream later than reimplemented per vendor. Defer to v0.4+ design. |
| ActivityWatch / HPI | ActivityWatch and HPI prove durable demand for local-first personal data systems, exportability, and extensibility. | HAI should copy support/export/recovery patterns, not their broad data-source ambition. |
| Fasten / HealthLog self-hosted PHRs | Fasten is self-hosted PHR/FHIR; HealthLog is self-hosted vitals/medication/AI report tooling. | PHR/EHR/provider and medication features are strategically wrong for HAI v1. Their support and backup posture is useful; their clinical surface is not. |
| Oura / WHOOP / Garmin / Gyroscope / Exist product surfaces | WHOOP and Oura expose conversational coach demand; Garmin shows AI insights as paid add-on; Gyroscope pushes all-in-one coach/food camera; Exist explicitly refuses AI and stresses export/privacy. | Demand exists for "ask my body data." HAI should refuse to become an all-in-one coach, food logger, or subscription dashboard; Exist is the better values analogue than Gyroscope. |

### Literature Ledger

| Source | Supports HAI | Challenges HAI | Add / delay / avoid | Stability |
|---|---|---|---|---|
| PHIA / Personal Health Insights Agent | Validates tool-using agents over raw LLM reasoning for wearable data. | Shows HAI needs stronger query/eval substrate for open-ended weekly claims. | Add W-PROV-1 and FActScore-shaped W58D. | Emerging but strong. |
| PHA / Anatomy of a Personal Health Agent | Confirms user demand spans data science, domain expertise, and coaching. | Multi-agent coaching scope exceeds HAI's settled boundaries. | Avoid multi-agent coach; borrow benchmark/task framing. | Emerging. |
| PH-LLM | Confirms sleep/fitness LLM benchmark value. | Model-centric fine-tuning is not HAI's route; HAI is runtime-first. | Add competitive-landscape doc; do not pivot to model training. | Stable enough as benchmark prior. |
| JITAI / EMI meta-analysis | Supports modesty about intervention effects. | Weakens any claim that recommendations alone create health outcomes. | Delay outcome claims until v0.5+ N-of-1 evidence. | Stable for near-term. |
| StudyU / StudyMe / SCED guide | Supports N-of-1 substrate and single-user evidence framing. | Requires protocol discipline before causal claims. | Add N-of-1 methodology doc before v0.5. | Stable. |
| AgentSpec / runtime enforcement | Gives language for HAI's code-owned rules and CLI contract. | Raises the bar for formalizing invariants. | Add "domain-pinned runtime enforcement" framing. | Emerging but strategically useful. |
| FActScore / MedHallu / factuality benchmarks | Supports atomic-claim, source-supported factuality. | Generic judges are insufficient. | W58D must be deterministic-first; include abstention metrics. | Stable. |
| LLM-as-judge limitations | Supports shadow mode, bias panels, and reference answers. | Contradicts any immediate blocking judge. | Delay W58J blocking until one release of shadow evidence. | Strong and growing. |
| MCP authorization/security specs + CVEs | Supports least privilege, no write surface, no project autoload, no hidden token paths. | MCP read surface is higher-risk than roadmap text implies. | Add W-MCP-THREAT before v0.3 PLAN.md. | Fast-moving, high-salience. |
| Wearable privacy systematic review | Supports local-first, no telemetry, explicit agent-provider caveat. | README privacy copy is less explicit than AGENTS/privacy doc. | Add honest agent-runtime exposure language. | Stable enough. |

---

## 4. Current Thesis — Whether It Still Holds

**Yes. Stronger than at v0.1.10.**

Each load-bearing claim, with what would falsify it:

| Claim | Hold strength (May 2026) | Falsifier |
|---|---|---|
| Skills never mutate actions; code never improvises coaching prose. | Strong. AgentSpec literature now names this pattern as state-of-the-art. | A skill PR lands that re-derives a band/score and slips through review. |
| Three-state audit chain is load-bearing. | Strong. No competitor (Open Wearables, WHOOP Coach, Hugo, Athletica) ships an analog. | A future workstream needs a four-state chain; current one cannot reconcile. |
| Local-first / no telemetry / single-user SQLite. | Strong. Apple Siri 2025 settlement + npj 2025 living systematic review of consumer-wearable privacy policies show "on-device" claims are routinely violated; HAI's posture is more conservative. | Regulator forces server-side audit logging incompatible with local-only, OR consumer hardware regresses on local LLM. |
| Refusal IS the demo. | Strong. MedHallu's "not sure" boost (+38% F1) + the JMIR AI 2024 systematic review on explainability + the gym-AI-hybrid pattern all point the same direction. | A user study (eventually, post-v0.5) shows defer prose actively reduces engagement without commensurate trust gains. |
| Interpretability > better recommendations (H1). | Anchored but unproven beyond N=1. JITAI meta-analysis g=0.15 backs "recommendations are a small lever" half. The "interpretability is a bigger lever" half is N=1-validated only. | Dom (post-v0.5+90d) consults underlying metrics over personal-evidence verdicts. Roadmap correctly schedules this falsification window. |

**Where the thesis is weakest:**

H1 ("interpretability > better recommendations") rides on N=1 evidence
plus inferred priors from JITAI / SePA. That is sufficient to commit to
the architecture; it is not yet sufficient to publish or pitch the
strategic claim externally. The v0.5 substrate plus 90-day measurement
remains the necessary falsification window — that schedule is correct
and should not be compressed.

**One framing upgrade the literature now allows:**

HAI should explicitly position itself as "domain-pinned AgentSpec for
personal health" in one external-facing doc (README opener and/or
strategic_plan_v1.md §1). The AgentSpec line of work (Wang/Poskitt/Sun
2025, ICSE '26) gives HAI a free vocabulary upgrade. Today's README
positions HAI against vendor coaches and bespoke architectures; in 2026
the cleaner external narrative is *"a runtime-enforcement framework
specialised to the six-domain personal-health surface."*

---

## 5. Top P0 Missing Capabilities

**P0 = blocks second-user trust, safety, governance, or roadmap
credibility.** All P0 items must land in v0.1.14 or as a v0.1.13.x
hardening release before v0.2.0 substrate work begins.

### P0-1 — Second-user empirical gate (W-2U-GATE)

**Gap.** v0.1.13 W-AA / W-AC / W-AF shipped the *test surface* for
onboarding (`hai init --guided` 7-step orchestrator + README quickstart
smoke test + acceptance matrix contract test). They have *not* been
empirically validated by a non-maintainer running a clean `pipx
install` on their own machine.

**Why P0.** "Trusted first value" is the v0.1.13 theme name (W-A1C7,
PLAN.md:60-71). Until a foreign user reaches `synthesized` state without
the maintainer's hands on the keyboard, the theme is unproven. Every
later workstream (W52 weekly review, W58 factuality gate, MCP read
surface) inherits this risk.

**Falsifier (i.e. what would make this *not* P0).** A live foreign-
machine onboarding session, recorded, with audit-chain output captured,
posted to the repo as a release artifact. v0.1.13 did not produce this.

**Recommended scope (W-2U-GATE, v0.1.14):**

- One recorded foreign-machine onboarding session by a non-maintainer
  (Dom's friend who saw the demo 2026-04-28 is the obvious candidate).
- Capture: terminal recording, time-to-`synthesized`, every place the
  user paused, every place they had to ask the maintainer.
- Output artifact: `reporting/docs/second_user_onboarding_2026-XX.md`
  with verbatim feedback + remediation plan.
- Acceptance: at least one full session reaches `synthesized` without
  maintainer intervention.

### P0-2 — Source-row provenance type (W-PROV-1)

**Gap.** Reconciliation §4 C10 calls source-row locators a
*first-class* concept for W52 weekly review, not added later. Today,
`recommendation_log` rows do not carry structured pointers to the
specific `state.db` rows that justified each quantitative claim. The
audit chain reconciles via `hai explain`, but a reader cannot follow
"why did the agent claim ACWR=1.6?" back to a specific
`running_session` row + computation step.

**Why P0.** W58's "deterministic claim-block" cannot work without this.
A factuality check needs a knowledge-source pointer; in HAI that
source is the local DB. Building W52 (v0.2.0) on the assumption that
provenance can be retrofitted is the most expensive sequencing error
available. Reconciliation §4 C10 already named this; it has not yet
moved into a v0.1.14 W-id.

**Falsifier.** A design doc that demonstrates W52 weekly-review claims
can be deterministically checked against the existing schema without
adding a `source_rows` JSON column or equivalent.

**Recommended scope (W-PROV-1, v0.1.14):**

- Schema design: `source_row_locator` value type
  (table+pk+column+row-version), surfaceable in `recommendation_log` +
  `proposal_log` + future `weekly_review` + `claim_block`.
- One end-to-end demonstration on a single domain (recovery R-rule
  firing) — proposal cites source rows; `hai explain` renders them;
  test asserts roundtrip. No weekly review yet.
- Migration 023 if needed.
- Acceptance: design doc + one-domain demo + 1 contract test.

### P0-3 — `hai explain` confusion-vs-clarity validation (W-EXPLAIN-UX)

**Gap.** JMIR AI 2024 systematic review on XAI in clinical decision
support shows explanations can *reduce* trust when confusing.
Tandfonline 2025 shows high-confidence calibrated outputs can also
*reduce* diagnostic accuracy via overreliance. HAI's `hai explain`
output is engineered for completeness; nobody has measured whether
that completeness reads as reassuring or overwhelming to a non-expert
reader.

**Why P0.** "Refusal IS the demo" only works if the refusal is
legible. If `hai explain` is dense or jargon-heavy, the same surface
that distinguishes HAI from WHOOP Coach also gates user trust.

**Falsifier.** A persona archetype "low domain knowledge user" reads
sample `hai explain` output and rates clarity above a defined floor.

**Recommended scope (W-EXPLAIN-UX, v0.1.14):**

- Add P13 persona archetype: low-domain-knowledge user (no athletics
  background, basic English, smartphone-native but not CLI-native).
- Manual review pass: run `hai explain` on three sample state
  trajectories; have the second-user (W-2U-GATE candidate) read the
  output and report what they understood, what confused them, what
  they wanted to know.
- Output artifact: `reporting/docs/explain_ux_review_2026-XX.md`.
- Acceptance: structured findings list; remediation
  recommendations folded into v0.2.0 W52 weekly-review prose design.

### P0-4 — MCP threat-model artifact (W-MCP-THREAT)

**Gap.** Strategic plan §10 schedules MCP exposure design at v0.3,
prereqs at v0.4, ship at v0.4-or-v0.5. The current scope contains no
threat-model artifact. The 2025-2026 MCP CVE/advisory class
(CVE-2025-59536/21852/6514/53109/53110, OWASP MCP Top 10 2026 beta,
OX Security's April 2026 STDIO disclosure, arXiv 2511.20920 academic
synthesis) makes "1-shot MCP integration" an actively documented
anti-pattern.

**Why P0.** The threat model is upstream of the design, not part of it.
If v0.3 starts with the design assuming a threat model can be authored
in parallel, the design will be wrong. AgentSpec / OWASP / arXiv 2511
all converge: "deterministic guardrails before exposed tool surface."

**Falsifier.** A draft threat-model document already exists. (It does
not.)

**Recommended scope (W-MCP-THREAT, v0.2.0 — *prerequisite for v0.3
plan-audit, not v0.3 implementation*):**

- `reporting/docs/mcp_threat_model.md` cataloguing each OWASP MCP
  Top 10 risk against HAI's planned read-surface; mapping to existing
  invariants where they hold; naming residual risks.
- Cite CVE-2025-59536 chain for "must not auto-load from project
  files."
- Cite Strava Nov 2024 ToS for "must not bridge AI to Strava data."
- Acceptance: first draft + one external review pass before v0.3
  PLAN.md is authored.

### P0-5 — Backup / restore / export canonical paths (W-BACKUP)

**Gap.** privacy.md §"Inspecting your data" surfaces SQL/JSONL
inspection, but there is no canonical command for `hai backup`,
`hai restore`, or structured `hai export`. The "deleting" section
mentions removing files; there is no "rotate state.db without losing
audit chain" path.

**Why P0.** A second user *will* corrupt their state.db within 90
days. Without a canonical recovery path, the response will be "I
guess I'll start over" — losing the audit chain and the H1 falsifier.

**Falsifier.** `hai doctor` already covers this. (It does not — doctor
is a *check*, not a recovery primitive.)

**Recommended scope (W-BACKUP, v0.1.14):**

- `hai backup [--dest path]` writes a versioned tarball of state.db
  + JSONL audit logs + capabilities snapshot + version stamp.
- `hai restore <tarball>` reverses, verifies migration version
  compatibility, refuses on schema mismatch.
- `hai export --format jsonl` emits a structured stream of all rows
  to stdout (already partially exists; consolidate).
- Acceptance: roundtrip test (backup → wipe → restore → identical
  `hai today` / `hai explain` output) passes in CI.

### P0-6 — *Withdrawn (Codex F-RES-01)*

The original draft made "honest second-user-exposure documentation"
a P0, claiming README.md did not duplicate the AGENTS.md hosted-agent
caveat. Verification at round-1 audit: README.md:34-38 already covers
this — *"If you drive the runtime with a hosted LLM agent, any context
you send to that host is governed by that host's data policy; Health
Agent Infra does not control the model provider."* The P0 is a false
positive. Privacy.md tightening is moved to §6 P2-5 as a doc-alignment
item, not a second-user trust blocker. **Five P0s remain.**

---

## 6. Top P1 / P2 Missing Capabilities

### P1-1 — FActScore-shaped atomic-claim decomposition for W58 (W-FACT-ATOM)

The literature (Min 2023, Pandit 2025) gives HAI an off-the-shelf
vocabulary for the W58 deterministic factuality gate: decompose
weekly-review prose into atomic claims, check each against the
provenance store from W-PROV-1. Today, W58 design (tactical_plan §6)
implies this shape but does not name FActScore as the prior art.

**Recommended:** v0.2.0 W58 design doc cites FActScore + MedHallu as
the published-pattern anchor; reports both with-abstention and
without-abstention metrics in the calibration eval scaffold.

### P1-2 — CALM judge-bias test panel (W-JUDGE-BIAS)

The LLM-judge bias literature (CALM meta-reviewer benchmark — Ye et
al. 2025 ICLR per Codex correction; primary-source verification
pending — plus Rating Roulette EMNLP 2025 self-inconsistency findings
plus No Free Labels arXiv 2503.05061) collectively make "shadow-then-
blocking judge" a defensible pattern, but only if the judge is
*bias-tested* before promotion. Today the judge promotion criterion
is "shadow evidence supports" (ROADMAP.md:47) without a defined
evidence shape.

**Recommended:** v0.2.0 ships a judge-bias test panel (position bias,
verbosity bias, score-rubric-order bias, length bias) that runs
against every shadow judgement; promotion to blocking requires named
bias thresholds met, not maintainer judgement. Specific numeric
thresholds are HAI-proposed acceptance gates (see §13 E-3),
*informed by* the bias literature but not derived from any single
benchmark — set per local validation.

### P1-3 — Persona archetype for trust-formation (P13 low-domain-knowledge)

Already named in P0-3 (W-EXPLAIN-UX) but worth listing separately
because the persona itself is reusable for v0.2.0 weekly-review prose
design.

### P1-4 — Data-source decoupling test (W-VENDOR-CHURN)

R-T-02 (vendor API churn) is rated "high likelihood over 24mo" in the
risk register. Mitigation today is "decoupled adapter design" + CSV
fallback. There is no test that *proves* the runtime works under a
single-source-broken simulated condition.

**Recommended:** v0.1.14 or v0.2.0 adds a test that simulates
"intervals.icu returns 5xx for 7 consecutive days" + "Garmin login
rate-limited" + "all manual intake only" and verifies persona matrix
still completes without crash; defer-rate increases honestly.

### P1-5 — Doc-only freshness automation extension (W-FRESH-EXT)

`test_doc_freshness_assertions.py` (added v0.1.12 W-AC) catches
version-tag drift mechanically. The two contradictions I caught in
ROADMAP.md (§8) were not version-tag drift — they were stale
*content* (referring to v0.1.9 weekly review and v0.2 BCTO). The
mechanical test cannot catch these without expansion.

**Recommended:** v0.1.14 hardening — extend
`test_doc_freshness_assertions.py` to grep ROADMAP.md / strategic_plan
/ tactical_plan for stale workstream IDs (e.g., any W52 reference
outside v0.2.0+ contexts is suspect). 1-day workstream.

### P2-1 — `reporting/docs/competitive_landscape.md`

The Phase 4 + Phase 5 research surfaced PHA / WHOOP Coach / Open
Wearables / Hugo / Athletica as the comparable landscape. Today
README.md does not name these directly; HYPOTHESES.md cites PHIA but
not PHA. A reader (or reviewer, or potential contributor, or grant
panel) cannot compare HAI to its peers in a single document.

**Recommended:** v0.2.0 ships a competitive-landscape doc citing PHA /
PHIA / SePA / Open Wearables / WHOOP Coach / Hugo with one-paragraph
each on how HAI is differentiated. Lifts text from §3 of this report.

### P2-2 — `reporting/docs/n_of_1_methodology.md`

StudyU / StudyMe / Vlaeyen 2024 SCED guide are stable methodology
priors for HAI's W49/W50 ledger work. v0.5 substrate work needs this
doc as foundation; authoring it earlier (v0.2.0) lets the v0.5 PLAN
inherit it.

**Recommended:** v0.2.0 doc-only deliverable, frames HAI's audit
chain as a single-user agent-mediated specialization of SCED.

### P2-3 — `expected_actions` per-domain enrichment (W-AK-2)

W-AK shipped declarative `expected_actions` per persona (v0.1.13).
Acceptance is "actions match whitelist." It does not yet test
*counterfactual* shape — "P11 stress override should escalate when X,
not when Y." This is the next maturation step.

**Recommended:** v0.1.14 or v0.2.0 light W-AK-2 — add
`expected_actions_when` parameterised tests (3-5 scenarios per
persona) layered on top of the v0.1.13 inline declaration. Cost
estimate: 2 days.

### P2-4 — Anti-fragility under host-LLM regression (W-HOST-FALLBACK)

R-X-04 (Anthropic / Claude Code direction change) is rated "medium
likelihood over 24mo." The mitigation is "CLI is portable." That is
true but unproven. No test verifies that the CLI works under a
local-LLM (Ollama / MLX) host agent.

**Recommended:** v0.2.0 or v0.3 ships a "host-portability" smoke test
that runs the CLI under at least one non-Anthropic local host agent
+ records the gaps. Not a release-blocker; insurance.

### P2-5 — privacy.md hosted-agent-exposure tightening (downgraded from P0-6)

The README hosted-agent caveat is already present at README.md:34-38
(verified per Codex F-RES-01). privacy.md could still benefit from a
parallel paragraph explicitly naming "agent-runtime exposure" as a
boundary the package does not control — symmetry with the README is
useful but not load-bearing. Estimated cost: 30-minute doc edit.
Bundle with the v0.1.14 doc-fix sweep.

---

## 7. Planned-but-Under-Scoped Items

These are workstreams currently named in the roadmap with insufficient
scope detail to ship cleanly.

| W-id | Cycle | Under-scoped because |
|---|---|---|
| **W-29** mechanical cli.py split | v0.1.14 | The boundary table in `reporting/docs/cli_boundary_table.md` exists and is W-29-prep green. The actual split *target* (1 main + 1 shared + 11 handler-group, each <2500 lines) is named in tactical plan but the *post-split test surface* (does `test_cli_parser_capabilities_regression.py` continue to byte-stable on the new module layout?) is not specified. Risk: split lands but capabilities snapshot regenerates and the byte-stability gate is silently weakened. |
| **W-Vb-3** 9-persona residual | v0.1.14 | The 9 personas are named (P2/P3/P6/P7/P8/P9/P10/P11/P12) but the *acceptance criteria* (what "ship-set" means for these 9) is inherited from v0.1.13's W-Vb wording and may need revision. P10 (adolescent) and P11 (elevated stress) carry domain-specific overrides that the v0.1.13 W-AK declarative contract handles, but the demo-replay path needs to re-validate them. |
| **W-AL** calibration scaffold | v0.1.14 | "Schema/report shape only" per ROADMAP, with correlation work to v0.5+. The schema needs to support FActScore-style atomic decomposition (see P1-1). If W-AL ships a calibration schema that doesn't anticipate atomic claims, v0.2.0 W58 will need a migration. |
| **W-AI** judge-adversarial fixtures | v0.1.14 | "Folds into W-AI" per RELEASE_PROOF.md:296 but the *adversarial corpus* (prompt-injection attempts, source-conflict cases, judge-bias probes from CALM taxonomy) is not enumerated. Without a corpus, "fixtures" defaults to whatever the maintainer thinks of, which is a known weak grounding signal. |
| **W52** weekly review | v0.2.0 | Strategic plan §7 names "source-row locators" but ties of to W-PROV-1. If W-PROV-1 does not land in v0.1.14, W52 is implicitly under-scoped because its acceptance depends on a primitive that isn't in the codebase yet. |
| **W58** deterministic claim-block + LLM judge | v0.2.0 | "Blocking from day 1" for the deterministic part; "shadow-by-default with HAI_W58_JUDGE_MODE flag" for the LLM part. The promotion criterion (when does the flag flip to blocking?) is "shadow evidence supports" — undefined. Per P1-2 above, this needs explicit evidence shape. |
| **W-30** capabilities-manifest schema freeze | v0.2.0 last-act | Per CP2 / D4 paired acceptance. The "freeze" semantics need definition — does it mean schema version pinned, or new fields require explicit migration, or full immutability? Tactical plan implies migration-with-version-bump but it's not concrete. |

---

## 8. Contradictions and Stale Docs

The contradiction hunt found one obvious count drift and the ROADMAP
re-read caught three narrative/dependency-chain drifts. All are minor
relative to the project's operating discipline — the v0.1.13 ship-time
freshness checklist held in 90%+ of canonical sites — but each is a
freshness violation worth fixing.

### C-DRIFT-01 (skill count)

**Site:** README.md:48 — "15 packaged markdown skills."
**Truth:** 14 (ls of skills/: daily-plan-synthesis, expert-explainer,
intent-router, merge-human-inputs, nutrition-alignment,
recovery-readiness, reporting, review-protocol, running-readiness,
safety, sleep-quality, strength-intake, strength-readiness,
stress-regulation).
**Severity:** low (user-facing but non-load-bearing).
**Fix:** README.md:48 → "14 packaged markdown skills." Doc-only.

### C-DRIFT-02 (stale Dependency Chain — v0.1.9 weekly review)

**Site:** ROADMAP.md:80 — "v0.1.9 weekly review".
**Truth:** Weekly review is W52, scheduled v0.2.0, not v0.1.9.
v0.1.9 shipped per CHANGELOG.md without weekly review.
**Severity:** medium — actively misleading; reader thinks weekly
review already shipped.
**Fix:** Rewrite ROADMAP.md "Dependency Chain" section (lines 79-90)
to reflect the current strategic-plan Wave structure
(v0.2.0 W52 → v0.3 MCP plan → v0.4 prereqs → v0.4-or-v0.5 MCP read →
v0.5 N-of-1 substrate → v0.6 estimator → v0.7 governed adaptation →
v1.0).

### C-DRIFT-03 (stale Dependency Chain — v0.2 BCTO)

**Site:** ROADMAP.md:81 — "v0.2 artifacts/BCTO".
**Truth:** "BCTO" (behaviour change technique ontology) is not a
current strategic-plan workstream. It does not appear in
strategic_plan_v1.md or tactical_plan_v0_1_x.md. It is an artifact
of the superseded multi_release_roadmap.md.
**Severity:** medium — references a phantom workstream.
**Fix:** Same rewrite as C-DRIFT-02 absorbs this.

### C-DRIFT-04 (stale Dependency Chain — first-run UX at v0.3)

**Site:** ROADMAP.md:82 — "v0.3 extension contracts + data-quality
drift + first-run UX".
**Truth:** First-run UX (W-AA `hai init --guided`) shipped in v0.1.13.
Data-quality drift was W-D2 in v0.1.10.
**Severity:** medium — claims unshipped what shipped.
**Fix:** Same rewrite as C-DRIFT-02 absorbs this.

### Note on reconciliation D1 vs CP5

I initially flagged ROADMAP.md showing v0.2.0 as a single substantial
release with intra-cycle judge flag (rather than the reconciliation D1
advisory 3-release split v0.2.0/v0.2.1/v0.2.2) as a contradiction. It
is *not* — CP5 (tactical_plan_v0_1_x.md:450) explicitly settled on
"single substantial release" post-reconciliation. ROADMAP and tactical
plan are aligned; reconciliation D1 was an advisory that the maintainer
overruled with reasoning. Documenting this here so a future reader does
not re-flag it.

### What this implies for ship-time freshness discipline

The freshness checklist (AGENTS.md "Ship-time freshness checklist (v0.1.12
W-AC / reconciliation A8)") catches *version-tag drift in the canonical
post-ship sites*. It does not catch *narrative/dependency-chain drift*
buried in a "this file is a high-level pointer" section. Recommendation:
W-FRESH-EXT (P1-5) extends `test_doc_freshness_assertions.py` to flag
references to W-ids and version numbers in informal sections.

---

## 9. Roadmap Revision Proposal

The current roadmap is internally coherent. Three structural revisions
would harden it.

### R-1 — Insert "v0.1.14 second-user gate" as the first workstream

**Why.** P0-1 (W-2U-GATE) ranks above every other v0.1.14 workstream
because every later v0.1.14 / v0.2.0 deliverable inherits the
foreign-machine-onboarding risk. Sequencing: W-2U-GATE first; W-29 cli.py
split, W-Vb-3, W-DOMAIN-SYNC, W-AI, W-AL after. If W-2U-GATE surfaces a
blocker (e.g., the foreign user can't get past `hai init --guided` step
4), v0.1.14 reshapes around the fix; downstream work remains in
roadmap.

**Acceptance:** W-2U-GATE folds into v0.1.14 PLAN.md as the first
workstream block in §2.

### R-2 — Move W-30 capabilities-manifest schema freeze out of v0.2.0

**Why.** v0.2.0 already carries W52 weekly review + W53 insight ledger
+ W58 deterministic claim-block + W58 judge shadow + a flag-flip
promotion criterion. Per CP5, the cycle is single-substantial-release
shape *because of design-coupling between W52 and W58*. W-30 is
schema-freeze hygiene; it has no design coupling to W52/W58. Adding it
to the same cycle expands D14 audit surface without coupling
benefit. Per D14 empirical settling, the v0.2.0 cycle is already the
biggest in HAI's history; the v0.1.13 cycle grew from 4→5 D14 rounds at
17 W-ids and v0.2.0 is plausibly larger.

**Recommended:** W-30 ships in v0.2.0.x or v0.2.1 hardening tier, *after*
the v0.2.0 substrate work has settled. CP6 (a new cycle proposal)
should formalise this; do not edit AGENTS.md D4 unilaterally.

**Falsifier:** A demonstrated W30↔W52/W58 coupling (e.g., the schema
freeze locks a field that W52 needs to introduce). I see no such
coupling in the strategic plan as currently written; if Dom or Codex
sees one, R-2 is wrong.

### R-3 — Pull MCP threat-model authoring forward to v0.2.0

**Why.** P0-4 (W-MCP-THREAT). If v0.3 starts MCP design without a
threat model already in tree, the design audit will surface what the
threat model would have surfaced — at the cost of a v0.3 D14 round.
The threat model is a design *input*, not output.

**Recommended:** v0.2.0 doc-only adjacent workstream (W-MCP-THREAT)
delivers `reporting/docs/mcp_threat_model.md`. Cost: ~3 days, single
maintainer. Folds into the "what should v0.3 plan against" question
that v0.3 PLAN.md will need to answer.

### R-4 — Annual hypothesis review schedule (anchor R-S-04)

R-S-04 calls for "annual hypothesis review." There is no schedule.
Recommended: v0.2.0 cycle ship-time deliverable is a 1-day H-update
review. This is part of operating discipline, not new code.

### Visual: revised roadmap (Path A — recommended; honors C6 + reconciliation D1)

```text
v0.1.13 (shipped 2026-04-30) — onboarding + governance prereqs
                |
                v
v0.1.14 (target Q3 mid; ~14 W-ids; 32-45 days — superseded from
30-40 per v0.1.14 D14 F-PLAN-R2-01)
  Tactical-plan baseline (per tactical_plan_v0_1_x.md:394-409):
    W-AH                   scenario fixture expansion (3-4d)
    W-AI                   ground-truth labelling methodology (2-3d)
    W-AJ                   LLM-judge harness scaffold (2-3d)
    W-AL                   calibration eval (2d)
    W-AM                   adversarial fixtures (1-2d)
    W-AN                   `hai eval run --scenario-set` CLI (1-2d)
    W-29                   [inherited] cli.py mechanical split (3-4d)
    W-Vb-3                 [inherited] 9-persona residual (4-6d)
    W-DOMAIN-SYNC          [inherited] L2 scoped contract test (0.5d)
  P0 additions (this report):
    W-2U-GATE              foreign-machine onboarding empirical proof (2-3d)
    W-PROV-1               source-row locator type + 1-domain demo (3-4d)
    W-EXPLAIN-UX           hai explain low-domain-knowledge review (2d)
    W-BACKUP               hai backup / restore / export (3-4d)
  P1 addition:
    W-FRESH-EXT            doc-freshness test extension (1d)
                |
                v
v0.2.0 (target Q4 2026; weekly review + deterministic factuality)
  W52                    weekly review with source-row locators (uses W-PROV-1)
  W58 deterministic      claim-block (blocking day 1)
  W-FACT-ATOM            FActScore-shaped atomic decomposition (folds into W58D)
  W-MCP-THREAT           [NEW] MCP threat-model artifact authoring (doc-only)
  W-COMP-LANDSCAPE       [NEW] competitive landscape doc (doc-only)
  W-NOF1-METHOD          [NEW] N-of-1 methodology doc (doc-only)
  W-2U-GATE-2            [NEW] second-user gate, second user
  Schema group: weekly-review tables + claim-block (one group)
                |
                v
v0.2.1 (target Q4 2026 / Q1 2027; insight ledger only)
  W53                    insight ledger
  Schema group: insight ledger tables (one group)
                |
                v
v0.2.2 (target Q1 2027; LLM judge shadow)
  W58 LLM judge          shadow-by-default
  W-JUDGE-BIAS           bias test panel (folds into W58J)
  Schema group: judge log tables (one group)
                |
                v
v0.2.3 (target Q1 2027 hardening; judge promotion + W-30)
  W58 LLM judge          flip from shadow to blocking (per bias panel pass)
  W-30                   capabilities-manifest schema freeze
  Schema group: none (flag flip + manifest pin)
                |
                v
v0.3 (MCP planning) → v0.4 (MCP prereqs) → v0.4-or-v0.5 (MCP read)
  | unchanged from current strategic plan §10 |
```

**Path B fallback:** if the maintainer overrides reconciliation C6
in favor of CP5 single-release, v0.2.0 carries W52 + W53 + W58D +
W58J shadow + W-30 in a single cycle (per ROADMAP.md:44-49 current
shape), at the cost of a 3-schema-group migration and a likely 5+
round D14 settling. That choice requires authoring a new CP that
explicitly overrides C6 with named reasoning.

---

## 10. v0.1.14 Recommended Changes

**Current named scope (tactical_plan_v0_1_x.md:394-409 — full
baseline; the original draft of this report enumerated only the
inherited subset):**

In-scope per tactical plan:

- W-AH — scenario fixture expansion (3-4 days).
- W-AI — ground-truth labelling methodology + maintainer review tool (2-3 days).
- W-AJ — LLM-judge harness scaffold, no model invocation yet (2-3 days).
- W-AL — calibration eval, confidence vs ground truth correlation (2 days).
- W-AM — adversarial scenario fixtures (1-2 days).
- W-AN — `hai eval run --scenario-set <set>` CLI surface (1-2 days).

Inherited from v0.1.13:

- W-29 — cli.py mechanical split (3-4 days, gated by W-29-prep green verdict).
- W-Vb-3 — persona-replay extension to 9 non-ship-set personas (4-6 days).
- W-DOMAIN-SYNC — scoped contract test (0.5 day).

Tactical-plan effort: **15-22 days for the 9-W-id baseline**
(tactical_plan_v0_1_x.md:436-437).

**Recommended additions (P0):**

- W-2U-GATE — foreign-machine onboarding empirical proof (2-3 days).
- W-PROV-1 — source-row locator type + 1-domain demo (3-4 days).
- W-EXPLAIN-UX — `hai explain` confusion-vs-clarity review (2 days).
- W-BACKUP — `hai backup` / `hai restore` / `hai export` (3-4 days).

**Recommended additions (P1):**

- W-FRESH-EXT — extend `test_doc_freshness_assertions.py` to grep
  for stale W-id references in informal doc sections (1 day).

**Recommended doc-only additions:**

- README.md:48 skill-count fix (15 → 14).
- ROADMAP.md "Dependency Chain" rewrite (lines 79-90).
- privacy.md hosted-agent-exposure tightening (P2-5; README.md:34-38
  already covers the README side per F-RES-01).

**Cycle tier classification (D15):**

Substantive. **14 W-ids total** (9 baseline + 5 P0/P1 additions),
**26-36 days estimated effort, round to 32-45 days with contingency**
(per v0.1.14 D14 F-PLAN-02 + F-PLAN-R2-01: arithmetic 31.5-44.5;
honest envelope 32-45).
Larger than v0.1.10 (~10 W-ids) but smaller than v0.1.13 (17 W-ids).
**D14 settling expectation: 4-5 rounds, unknown empirical settling
shape for "pre-PLAN-revision new-W-id density"; do not assume the
4-round 10→5→3→0 norm.** v0.1.13 settled at 5 rounds for 17 W-ids;
v0.1.14 at 14 W-ids with 5 newly-introduced P0s should expect 4-5
rounds.

**Contingency clause:** if W-2U-GATE surfaces a structural blocker
(e.g., the foreign user cannot complete `hai init --guided`),
v0.1.14 reshapes around the fix; downstream work moves to v0.1.15
without prejudice.

**Rejected additions:**

- ❌ Any v0.2.0 W52/W58 design work. Hold this for the v0.2.0 PLAN.md
  authoring once the v0.1.14 substrate (W-PROV-1) is in tree.
- ❌ MCP planning. Defer until W-MCP-THREAT lands in v0.2.0.
- ❌ A test fix for the C-DRIFT-04 contradiction in ROADMAP without a
  rewrite. Patching one line continues the rot.

**Acceptance criteria for cycle ship:**

- All P0 W-ids close (not partial-closure).
- D14 verdict `PLAN_COHERENT` within **≤5 rounds**; if it exceeds 5
  rounds, maintainer re-scopes the cycle before implementation.
  (Round-2 audit F-RES-R2-02 flagged the original `≤4 rounds` gate as
  contradicting the §10 4-5 rounds expectation for a 14-W-id cycle.)
- IR verdict `SHIP` or `SHIP_WITH_NOTES` within ≤3 rounds.
- W-2U-GATE artifact exists in `reporting/docs/`.
- `test_cli_parser_capabilities_regression.py` byte-stable through
  the W-29 split.
- Persona matrix re-runs clean post-W-Vb-3 (12 personas, 0 findings).

**Falsifier (this v0.1.14 plan is wrong if):**

- W-2U-GATE surfaces a structural blocker that requires a v0.1.13.x
  hotfix before v0.1.14 substrate work can proceed. (Treat that as a
  good outcome — better to surface it now.)
- W-PROV-1 design needs a major schema change (not just migration
  023) — would imply v0.1.14 should be split into substrate and
  feature halves.

---

## 11. v0.2.0 Split Recommendation

### The C6 vs CP5 tension

The original draft of this report claimed CP5 had settled v0.2.0 as a
single substantial release. Codex round-1 audit (F-RES-03) correctly
flagged that this conflates two separate constraints:

- **CP5** (tactical_plan_v0_1_x.md:441-501): single-release shape,
  argued from **W52↔W58 design coupling** — claims surface + claim-
  check primitive should not ship apart.
- **C6** (reconciliation.md:147): "**One conceptual schema group per
  release.**" — the gap detector trips when 3 schema groups land in
  one migration burst.

CP5 did not engage with C6. The two are in tension because v0.2.0's
substrate carries 3 conceptual schema groups (weekly-review tables,
insight ledger tables, judge log tables) — single-release respects
CP5 but violates C6; 3-release respects C6 but partially violates
CP5's design-coupling argument.

### Path A — recommended (4-release per reconciliation D1, strict C6)

Round-2 audit (F-RES-R2-01) correctly flagged that a 3-release Path A
left v0.2.1 carrying two schema groups (insight ledger + judge log),
violating C6. The original draft self-flagged this as "borderline" but
that is not the same as honouring C6. The strict-C6 split is four
releases:

| Release | Scope | Schema group | Cost (days) |
|---|---|---|---|
| **v0.2.0** | W52 weekly review + W58D deterministic claim-block + W-FACT-ATOM atomic decomposition + 4 doc-only adjuncts (W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD, W-2U-GATE-2) | weekly-review tables + claim-block (**one group**) | 18-24 |
| **v0.2.1** | W53 insight ledger | insight ledger tables (**one group**) | 8-12 |
| **v0.2.2** | W58J LLM judge shadow + W-JUDGE-BIAS bias test panel | judge log tables (**one group**) | 8-12 |
| **v0.2.3** | W58J flip from shadow to blocking + W-30 capabilities-manifest schema freeze | no new schema (flag flip + manifest pin) | 5-8 |

CP5's W52↔W58 coupling is preserved in v0.2.0 (W52 + W58D ship
together). The shadow-then-blocking judge evolution is staged across
v0.2.2 → v0.2.3 — itself a flag-flip pattern, not a coupled primitive.
Total Path A v0.2.x effort: **39-56 days** across four cycles.

### Path B — fallback (single-release per CP5 with new CP overriding C6)

Honors CP5 exactly; requires authoring a new CP that explicitly
overrides C6 with named reasoning (e.g., "W52 source-row locator
schema is shared with W53 insight ledger and W58 claim block;
splitting forces N-1 unsupported migrations against the gap
detector"). Single v0.2.0 ships W52 + W53 + W58D + W58J shadow + W-30
in 30-39 days.

### Recommendation

**Path A.** Reasoning:

- C6 is a correctness constraint (the gap detector *will* trip on a
  3-schema-group migration); CP5 is a sequencing preference.
- W52↔W58D coupling is preserved by Path A; only W58J's shadow-
  evolution splits, and that is itself a phase-by-phase rollout
  pattern.
- Smaller per-cycle D14 audit surface — three 4-round cycles is
  empirically cheaper than one 5-6 round cycle.
- The reconciliation document's D1 synthesis already proposed this
  shape; honoring it requires no new design work.

**Falsifier (Path A is wrong if):** v0.1.14 W-PROV-1 doesn't land
cleanly, OR v0.2.0 W52 design reveals an irreducible schema coupling
to W53 that the reconciliation didn't anticipate. In either case
the v0.2.0 PLAN.md authoring (which runs its own D14) will surface
this and the maintainer can revise.

### Out (regardless of Path A vs B)

W-30 capabilities-manifest schema freeze ships *after* the substrate
work, not as the last act of the substrate cycle. Path A places it
in v0.2.2; Path B requires a separate v0.2.0.x or v0.2.1 hardening
release.

---

## 12. Second-User Readiness Plan

The single largest hidden risk in the project. v0.1.13 shipped the test
surface; the empirical proof remains future work.

**Workstream catalogue:**

1. **W-2U-GATE (v0.1.14)** — first foreign-machine session. Output
   artifact + remediation list.
2. **W-EXPLAIN-UX (v0.1.14)** — same user reads sample `hai explain`
   output. Output artifact + remediation list.
3. **W-BACKUP (v0.1.14)** — backup/restore/export primitives.
4. **W-2U-GATE-2 (v0.2.0)** — second foreign-machine session,
   different user, after v0.1.14 remediation. Output: comparison
   doc; what improved, what regressed, what's new.
5. **P13 persona archetype (v0.1.14)** — low-domain-knowledge user
   in the matrix.
6. **`hai support` or equivalent (v0.2.0)** — bundle a state.db +
   audit logs + version stamp into a redacted tarball the user can
   share with the maintainer to debug. Privacy-respecting (no
   intent text, no goals, just structure + counts).

**Acceptance criteria for "second-user-ready":**

- Two distinct foreign users have reached `synthesized` state on
  their own machines without maintainer intervention.
- One foreign user has run for ≥7 consecutive days without
  abandoning the tool.
- One foreign user has hit a real bug; their `hai support` bundle
  was sufficient for the maintainer to diagnose without further
  back-and-forth.

**What this is *not*:**

- A pivot to multi-user. Single-user-local remains the architecture.
- A growth or marketing initiative. The maintainer remains the only
  evangelism path.
- A claim that HAI is "ready for general use." Two users is N=2; the
  literature requires more for any externalisable claim.

---

## 13. Evaluation and Calibration Plan

The literature gives HAI a clean published vocabulary; the current eval
strategy doc (eval_strategy/v1.md) needs three tweaks before v0.2.0
W58 design begins.

### E-1 — Adopt FActScore vocabulary in W-FACT-ATOM

Min 2023's FActScore decomposes generation into atomic facts and
checks each against a knowledge source. HAI's "knowledge source" is
`state.db` + `core/research/` + classify-state derivation. Recommended
v0.1.14 W-AL design references FActScore; v0.2.0 W58 implements
atomic decomposition.

### E-2 — Adopt MedHallu's abstention-aware metric

Pandit 2025's MedHallu shows abstention category boosts F1 by up to
38%. HAI must report calibration *both with and without* abstention.
"Refusal IS the demo" demands it.

**Recommended metric set (v0.2.0):**

- Atomic-claim factuality precision (without abstention).
- Atomic-claim factuality precision *with* "won't fabricate"
  branch.
- Abstention rate per domain.
- Confidence-calibration correlation (post-v0.5+90d only — not
  reportable yet).

### E-3 — Bias panel for the LLM judge (HAI-proposed thresholds)

The LLM-judge bias literature (CALM meta-reviewer benchmark — Ye et
al. 2025 ICLR per Codex F-RES-05 correction; primary-source
verification pending — plus Rating Roulette EMNLP 2025 on self-
inconsistency, plus No Free Labels arXiv 2503.05061 on ungrounded
judge under-calibration) names *categories* of bias HAI's eventual
LLM judge must be tested against. The literature does *not* derive
specific numeric promotion thresholds.

The thresholds below are **HAI-proposed acceptance gates**, informed
by but not derived from the bias literature. They should be set per
local validation against the v0.1.14 W-AI / W-AM judge-adversarial
fixtures, not adopted as literature results.

Promotion to blocking requires (proposed):

- Position bias < 5% under shuffled-input shadow runs.
- Verbosity bias < 10%.
- Score-rubric-order bias < 5%.
- Reference-answer bias < 5%.
- Self-consistency ≥ 0.8 under repeated sampling.

If a single proposed gate fails, judge stays in shadow. The
maintainer cannot manually override (the bias is the override
criterion). Thresholds are revisable per v0.2.1 W-JUDGE-BIAS
empirical findings; setting them in PLAN.md is the design moment.

### E-4 — Hard ceiling realism

MedHallu's GPT-4o cap of F1=0.625 on hard medical hallucinations is
the empirical ceiling for HAI's first calibration numbers. The
public release should not claim better; it should claim *honest*.
v0.2.0 ship-time success-framework update should set the bar
accordingly.

### E-5 — Defer human-grounded calibration

No Free Labels (arXiv 2503.05061) shows ungrounded LLM-as-judge
under-calibrates. HAI's N=1 grounding (Dom himself) is a known
weak link. The roadmap correctly defers human-grounded calibration
to v0.5+ (post-substrate). v0.2.0 should not claim "calibrated" —
only "shadow-tested."

---

## 14. Security, MCP, and Privacy Plan

### S-1 — Document HAI's structural advantage *as the OWASP-MCP-aligned reference shape*

> **Round-1 Codex audit F-RES-04:** the original draft's item-by-item
> mapping below was authored from secondary research; Codex flagged
> several items mapped to the wrong OWASP MCP slot. **The mapping is
> marked PENDING RE-VERIFICATION against the OWASP source
> (https://owasp.org/www-project-mcp-top-10/) and must be rebuilt
> before being used as an external-narrative-grade artifact.** Per
> Codex, the current OWASP MCP Top 10 enumeration is: MCP01 Broken
> Authentication/Authorization, MCP02 Token Theft, MCP03 Tool
> Poisoning, MCP04 Excessive Permissions, MCP05 Command Injection,
> MCP06 Indirect Prompt Injection, MCP07 Sensitive Information
> Disclosure, MCP08 Rug Pulls, MCP09 Tool Shadowing, MCP10 Tool
> Metadata Spoofing. Re-verify both Codex's enumeration and the
> HAI alignment before W-MCP-THREAT cites it.

The strategic claim — *HAI's existing invariants align cleanly with
the OWASP MCP Top 10 surface* — does not depend on the exact item
numbering. Whatever the verified order, HAI ships:

- Tokens in OS keyring, scoped per source.
- Capabilities manifest + mutation-class taxonomy (no excessive
  permissions).
- Deterministic CLI surface, no shell-out from skills (no command
  injection).
- Skill prompts are package-bundled (no indirect prompt injection
  via user-supplied tool descriptions).
- Per-source OAuth, no shared service-role token (no broken auth).
- Three-state audit chain via `hai explain` (no insufficient logging).
- Only one "MCP server" (the CLI), no plugin loading from project
  files (no rug pulls, no tool shadowing).
- Single-user local SQLite (no sensitive-information disclosure
  cross-user).
- Capabilities-manifest schema-freeze (W-30) is the response to
  tool-metadata-spoofing / tool-poisoning when MCP exposure ships.

**Recommended v0.2.0 doc:** `reporting/docs/owasp_mcp_alignment.md`,
authored *after* the OWASP source is re-verified and the mapping is
rebuilt. Until then, this section is internal-strategy material, not
external-narrative-grade.

### S-2 — MCP threat-model authoring before v0.3

Detailed in P0-4 (W-MCP-THREAT). Anchored on:

- CVE-2025-59536 / CVE-2026-21852 (project-file MCP autoload + token
  exfiltration).
- CVE-2025-6514 (mcp-remote command injection via malicious
  authorization endpoint).
- CVE-2025-53109 / 53110 (Anthropic Filesystem-MCP server
  symlink-bypass + prefix-match path traversal).
- OX Security's April 2026 MCP STDIO disclosure (configuration-to-
  command execution across SDK usage patterns).
- arXiv 2511.20920 (academic synthesis of MCP threat landscape).

I am intentionally not relying on the previously circulated 22% / 43%
aggregate MCP-vulnerability figures; I did not verify their primary
source during this pass. The CVE/advisory evidence alone is enough to
make the threat-model prerequisite non-optional.

### S-3 — Honest agent-runtime-exposure language (status: ALREADY SHIPPED)

Per F-RES-01 verification: README.md:34-38 already names hosted-LLM-
agent context exposure as a boundary the package does not control.
AGENTS.md governance invariant #4 has the parallel statement.
Apple Siri 2025 settlement is a cautionary anchor for honesty
elsewhere; not a remediation prompt for HAI. privacy.md tightening is
P2-5 (doc-alignment), not a blocker.

### S-4 — Strava ToS guard

Strava's Nov 2024 API agreement prohibits AI/ML use of Strava data
and named intervals.icu specifically. HAI today defaults to
intervals.icu; intervals.icu's own Strava sync is downstream.
Recommended: `reporting/docs/data_source_governance.md` documenting
which sources can be used in AI-mediated workflows. Light v0.2.0
artifact.

### S-5 — Dependency / supply-chain hardening

See §17.

---

## 15. Data-Source and Provenance Plan

### D-1 — Source-row locator type (W-PROV-1, v0.1.14)

Detailed in P0-2.

### D-2 — Pull-adapter contract documentation

`reporting/docs/how_to_add_a_pull_adapter.md` exists; verify it covers
the source-row locator emission contract once W-PROV-1 lands.

### D-3 — Multi-source reconcilement contract

If v0.4 broadens beyond intervals.icu + Garmin to (e.g.) Open
Wearables as upstream, the reconciliation rules need explicit
documentation. Today the "evidence contract" per AGENTS.md "Do Not
Do" line is not broadened. Defer until needed.

### D-4 — Don't add Strava

Per S-4. Add to AGENTS.md "Do Not Do" if not already there.

### D-5 — Don't depend on Garmin Connect screen-scraping for default

Settled decision D5 already covers this. Multiple community Garmin
MCPs exist (per April 2026 web search); the leading ones reuse the
`python-garminconnect` SSO library, which inherits the per-account
429 rate limit. Specific project counts and dependency chains require
a sourced inventory before audit-grade citation (Codex F-RES-09
removed the unsourced "8+ / all" claim from the original draft).
HAI's intervals.icu default is correct regardless of the count.

### D-6 — Open Wearables consideration

Open Wearables (MIT, single-org self-hosted,
Postgres+Celery+Docker) is the closest peer. Their MCP server is
*upstream-able* — HAI could in v0.4+ consume their normalised wearable
data rather than mint adapters per-vendor. Not in current scope; flag
for v0.4 PLAN.md design phase.

---

## 16. Support, Backup, Export, and Recovery Plan

### Sup-1 — `hai backup` / `hai restore` / `hai export` (W-BACKUP)

Detailed in P0-5.

### Sup-2 — `hai support` redacted bundle

For the second-user case where the user can't reproduce + the
maintainer needs structured state to debug. Bundle: schema version,
table row counts (no PII), recent runtime_event_log, capabilities
snapshot, no intent text, no goal text. Recommended v0.2.0.

### Sup-3 — Migration version-mismatch refusal

If a user installs a wheel newer than their state.db migration
version, `hai doctor` should refuse cleanly with a documented
recovery path. Verify v0.1.13 already does this; if not, hardening
ticket.

### Sup-4 — Recovery doc

`reporting/docs/recovery.md` — step-by-step for state.db corruption,
keyring loss, intervals.icu credential rotation, schema-mismatch.
Recommended v0.1.14 doc-only.

### Sup-5 — `hai doctor --deep` extension scope

W-AE shipped 5-outcome probe classification for intervals.icu. For
v0.2.0+: extend the probe-class taxonomy to cover state.db integrity,
JSONL tail-corruption, capabilities-manifest mismatch.

### Sup-6 — `hai eval review` tool

eval_strategy/v1.md:233-234 references this. Verify scope; if it lets
the maintainer flag scenario expected output, that's the right shape.
If not yet built, schedule for v0.1.14.

---

## 17. Release Trust / Supply-Chain Plan

The ship-time freshness checklist + RELEASE_PROOF.md discipline is
strong. The supply-chain layer below is less hardened.

### Sc-1 — Pinned dependency tree

Verify `uv.lock` is checked in and frozen at ship time. (Likely yes;
verify.)

### Sc-2 — Wheel signing

PyPI now supports trusted publishing via OIDC (sigstore). HAI uses
`twine upload` per `reference_release_toolchain.md`. Recommended:
v0.2.0 or v0.3 cycle ships GitHub Actions OIDC trusted-publishing
setup; reduces credential-exposure risk in the release toolchain.

### Sc-3 — SBOM generation

Bandit + ruff + mypy gate dependencies. There is no CycloneDX or
SPDX SBOM. Not P0; flag for v0.4 (when external contributor scrutiny
is more likely).

### Sc-4 — `python-garminconnect` upstream risk

D5 settled "Garmin not default live source." `python-garminconnect`
remains the SSO library; per Phase 4 research, it inherits the
per-account 429. v0.4 cycle should re-evaluate dependency: keep, fork,
or replace.

### Sc-5 — Anthropic / Claude Code upstream risk

R-X-04 rated medium-likelihood-over-24mo. CVE-2025-59536 / CVE-2026-21852
specifically targeted Claude Code's MCP autoload. HAI runs *inside*
Claude Code as the daily driver; mitigation is the local-stdio /
no-autoload posture. Verify HAI never ships a `.claude/settings.json`
that auto-loads anything; adopt as `Do Not Do` in AGENTS.md if not
explicit.

### Sc-6 — Skill-installation review

`hai setup-skills` copies skills tree into `~/.claude/skills/`.
Verify it doesn't shell-out, doesn't autoload, doesn't fetch from
network. Single-day audit.

---

## 18. What Not to Build

These are recommendations to *refuse*. Each requires reopening a
settled decision — i.e., a formal CP — to override. Most have a
named-vendor failure mode.

| Anti-pattern | Vendor / paper failure mode | Settled-decision link |
|---|---|---|
| Hosted multi-user backend. | Bearable / Gyroscope / Exist.io: pretty dashboards, no refusal layer. Mirth Connect 4.6: closed source after community adoption. OWASP-MCP-pattern: sensitive information disclosure across users (cf. §14 S-1 pending verification). | AGENTS.md governance invariant #4. |
| Autonomous training-plan generation. | WHOOP Coach (OpenAI-mediated, no determinism). Hugo / Athletica (write plans, complaints about nondeterminism). | AGENTS.md "Do Not Do" + governance invariant #2. |
| Autonomous diet-plan generation. | Same family. | AGENTS.md "Do Not Do" + nutrition v1 macros-only D6. |
| Clinical claims / diagnosis prose. | Apple App Store medical-device-status disclosure policy (effective by 2027; trade press, not regulator action — see §3 Apple framing). Oura / WHOOP wellness-disclaimer pattern. Local invariant is the load-bearing anchor; FDA general-wellness boundary + AGENTS.md non-goals are the primary basis. | AGENTS.md governance invariant #3. |
| Strava-anchored data path. | Strava Nov 2024 ToS prohibits AI/ML use; intervals.icu specifically named. | New addition needed to AGENTS.md "Do Not Do". |
| MCP autoload from project files. | CVE-2025-59536 / CVE-2026-21852 (Check Point). | New addition needed to AGENTS.md "Do Not Do". |
| Threshold mutation without explicit user commit. | AgentSpec literature: "deterministic guardrails before exposed mutation surface." | W57 governance invariant + D13 threshold-injection seam. |
| Multi-tenant deployment. | Mirth-Connect-style closure, plus all OWASP-MCP shared-credential risks. | AGENTS.md governance invariant #4. |
| 60+ raw vendor-API tools surfaced to LLM. | `Nicolasvegam/garmin-connect-mcp` (61 tools), `eddmann/garmin-connect-mcp` (22 tools). Tool poisoning + skills-doing-arithmetic anti-pattern. | AGENTS.md "skills never compute bands/scores." |
| Hosted MCP relay distributing tokens. | OWASP-MCP-pattern: token theft + sensitive disclosure + metadata spoofing (cf. §14 S-1 pending verification). Supabase Cursor service-role-token exfiltration incident (mid-2025). | AGENTS.md governance invariant #4. |
| `hai capabilities` schema freeze before W52/W58 land. | Field-locking before features need fields = forced migration on first new field. | AGENTS.md D4 (W30 scheduled v0.2.0 last). |
| LLM-judge promotion to blocking before bias panel passes. | No Free Labels + CALM + Rating Roulette literature. | New addition needed; tactical_plan §6 already implies. |
| Smart notification scheduling / nudge-tuning features. | 2025 JITAI meta-analysis g=0.15 + burnout literature. The complexity is not justified by the published effect size. | Out of scope; flag if proposed. |
| Strava-equivalent "social" surface. | Out of scope by H2. | AGENTS.md non-goals. |
| Web/mobile dashboard. | Open Wearables / Bearable / etc. occupy this lane. | AGENTS.md non-goals + ROADMAP.md "Explicitly Out Of Scope." |
| Hidden learning loop / automatic threshold mutation from outcomes. | AgentSpec runtime-enforcement literature explicitly documents this as anti-pattern for governed agents. | ROADMAP.md "Explicitly Out Of Scope." |

---

## 19. Open Decisions for Dom

These need a maintainer call before v0.1.14 PLAN.md ships. Auto-mode
default in brackets.

1. **OQ-A — Accept v0.1.14 P0 additions (W-2U-GATE, W-PROV-1, W-EXPLAIN-UX,
   W-BACKUP, W-FRESH-EXT)?** [Default: yes; they're all under 5-day
   workstreams individually.]
2. **OQ-B — Choose v0.2.0 split path: Path A (4-release strict-C6 split:
   v0.2.0 W52+W58D / v0.2.1 W53 / v0.2.2 W58J shadow / v0.2.3 W58J
   promote + W-30) or Path B (single-release per CP5 with new CP
   overriding C6)?** [Default: Path A; honors both CP5's W52↔W58
   coupling argument and C6's strict one-schema-group-per-release
   constraint. Round-2 audit F-RES-R2-01 corrected the 3-release
   Path A to 4-release.]
3. **OQ-C — Pull MCP threat-model authoring forward to v0.2.0 as
   W-MCP-THREAT?** [Default: yes; doc-only, low cost, high value as
   v0.3 PLAN.md input.]
4. **OQ-D — Add P13 low-domain-knowledge persona archetype before
   v0.1.14 ships?** [Default: yes; W-AK declarative-actions
   contract makes this cheap.]
5. **OQ-E — Author `competitive_landscape.md` + `n_of_1_methodology.md`
   in v0.2.0?** [Default: yes; lifts text from this report; no new
   research required.]
6. **OQ-F — Add Strava-ToS / MCP-autoload / threshold-mutation rules
   to AGENTS.md "Do Not Do"?** [Default: yes; one-paragraph addition.]
7. **OQ-G — Author `mcp_threat_model.md` BEFORE v0.3 PLAN.md, even if
   it means delaying the v0.3 PLAN-audit by a cycle?** [Default: yes;
   the literature anchors this.]
8. **OQ-H — Schedule annual hypothesis review at v0.2.0 ship?**
   [Default: yes; aligns R-S-04 mitigation.]
9. **OQ-I — Designate the 2026-04-28-demo recipient (Dom's friend) as
   the W-2U-GATE first foreign user?** [Default: ask first.]
10. **OQ-J — Adopt "domain-pinned AgentSpec for personal health"
    framing in README.md opener?** [Default: maintainer choice;
    framing change, not architecture change.]
11. **OQ-K — Promote LLM judge to blocking by quantitative bias panel
    rather than maintainer judgement?** [Default: yes; bias-literature-
    informed, with HAI-proposed thresholds validated locally.]
12. **OQ-L — Accept the FActScore + MedHallu vocabulary for the
    calibration-eval design doc?** [Default: yes; published prior art.]
13. **OQ-M — Should `hai support` (redacted state bundle) land in
    v0.1.14 or v0.2.0?** [Default: v0.2.0; v0.1.14 is already full.]
14. **OQ-N — Re-verify OWASP MCP Top 10 mapping against
    https://owasp.org/www-project-mcp-top-10/ before W-MCP-THREAT
    cites it?** [Default: yes; doc-fix-sweep work. Codex F-RES-04
    flagged the original mapping as inaccurate.]
15. **OQ-O — Schedule a retrospective on the research-audit pattern
    after the next strategic-research cycle uses it (or doesn't),
    before considering D16 status?** [Default: yes. Per Codex F-RES-10,
    promoting this audit shape to a settled decision on N=1 evidence
    would violate the project's own settled-decision discipline.]

---

## 20. Candidate Workstream Catalogue

ID | Cycle | Acceptance criteria | Files likely touched | Cost (days)

### v0.1.14

**W-2U-GATE** (P0)
- *Acceptance:* one foreign user reaches `synthesized` on own machine without maintainer intervention; recorded session + remediation list filed.
- *Files:* `reporting/docs/second_user_onboarding_2026-XX.md` (new), possibly cli.py / init/ if remediation surfaces a real bug.
- *Cost:* 2-3 days (mostly coordination + writing).

**W-PROV-1** (P0)
- *Acceptance:* schema design doc + 1-domain demo (recovery R-rule cites source rows; `hai explain` renders them; roundtrip test).
- *Files:* `core/state/migrations/023_source_row_locator.sql` (new), `core/writeback/proposal.py`, `core/explain/render.py`, `verification/tests/test_source_row_locator_recovery.py` (new), `reporting/docs/source_row_provenance.md` (new).
- *Cost:* 3-4 days.

**W-EXPLAIN-UX** (P0)
- *Acceptance:* P13 persona added; one foreign user reads sample `hai explain` output; structured findings doc filed.
- *Files:* `verification/dogfood/personas/p13_low_domain_knowledge.py` (new), `reporting/docs/explain_ux_review_2026-XX.md` (new).
- *Cost:* 2 days.

**W-BACKUP** (P0)
- *Acceptance:* `hai backup` / `hai restore` / `hai export` round-trip test passes in CI; `reporting/docs/recovery.md` exists.
- *Files:* `cli.py` (new subparsers), `core/backup/` (new module), `verification/tests/test_backup_restore_roundtrip.py` (new), `reporting/docs/recovery.md` (new).
- *Cost:* 3-4 days.

**W-FRESH-EXT** (P1)
- *Acceptance:* `test_doc_freshness_assertions.py` rejects W-id references in informal-section sites that don't match active workstreams; ROADMAP.md C-DRIFT-02/03/04 fixes go through this gate.
- *Files:* `verification/tests/test_doc_freshness_assertions.py`, ROADMAP.md.
- *Cost:* 1 day.

**W-29** (held)
- *Acceptance:* cli.py split (1 main + 1 shared + 11 handler-group, each <2500 lines); `test_cli_parser_capabilities_regression.py` byte-stable through the split.
- *Files:* `cli.py` → split into `cli/__init__.py` + `cli/_shared.py` + 11 handler files.
- *Cost:* 3-4 days mechanical refactor.

**W-Vb-3** (held)
- *Acceptance:* 9 non-ship-set personas reach `synthesized`; `expected_actions` declarative contract enforced.
- *Files:* `verification/tests/test_demo_persona_replay_end_to_end.py`, possibly fixtures under `verification/tests/_fixtures/`.
- *Cost:* 2-3 days.

**W-DOMAIN-SYNC** (held)
- *Acceptance:* L2 scoped contract test ensures the 8 hardcoded registry enumerations (per reconciliation L2) stay in sync.
- *Files:* `verification/tests/test_domain_sync_contract.py` (new).
- *Cost:* 2 days.

**W-AI** (held)
- *Acceptance:* judge-adversarial fixture corpus covers prompt-injection / source-conflict / CALM-bias-probe categories; ≥10 fixtures per category.
- *Files:* `verification/tests/_fixtures/judge_adversarial/` (new), `verification/tests/test_judge_adversarial.py` (new).
- *Cost:* 3 days.

**W-AL** (held)
- *Acceptance:* calibration-eval schema (FActScore-aware) + report shape; no correlation work.
- *Files:* `core/eval/calibration_schema.py` (new), `reporting/docs/calibration_eval_design.md` (new).
- *Cost:* 2-3 days.

**Plus the tactical-plan baseline (per tactical_plan_v0_1_x.md:394-401):**

- W-AH (3-4d), W-AI (2-3d), W-AJ (2-3d), W-AL (2d), W-AM (1-2d),
  W-AN (1-2d) — eval-substrate set, 11-16 days.

**v0.1.14 cycle estimate:** **32-45 days** (revised from 30-40 per
v0.1.14 D14 F-PLAN-R2-01; arithmetic 31.5-44.5) (1 maintainer; 14 W-ids
total: 9 baseline + 5 P0/P1 additions). Cycle tier: substantive. D14
expectation: 4-5 rounds (empirical settling shape unknown for this
new-W-id density; do not assume 4-round norm). Original draft's
23-29-day / 10-W-id estimate revised per Codex F-RES-02.

### v0.2.0 (Path A — recommended; weekly review + deterministic factuality)

**W52** weekly review with source-row locators (uses W-PROV-1 from v0.1.14)
- *Acceptance:* `hai weekly` produces a 7-day summary; every quantitative claim cites source rows; `hai explain weekly` reconciles.
- *Files:* `core/weekly/` (new), `cli.py`, migration 024, `verification/tests/test_weekly_review.py` (new).
- *Cost:* 7-10 days.

**W58 deterministic** claim-block (blocking from day 1)
- *Acceptance:* every weekly-review claim is decomposable; deterministic check passes/fails per claim; failures block prose render.
- *Files:* `core/factuality/` (new), `verification/tests/test_w58_deterministic.py` (new).
- *Cost:* 5-7 days.

**W-FACT-ATOM** FActScore-shaped atomic decomposition
- *Folds into W58 deterministic.* +1 day overhead vs naive design.

**W-MCP-THREAT** doc-only adjunct
- *Acceptance:* `reporting/docs/mcp_threat_model.md` filed; OWASP MCP Top 10 mapping verified against primary source first (per F-RES-04).
- *Cost:* 3 days.

**W-COMP-LANDSCAPE** doc-only adjunct
- *Acceptance:* `reporting/docs/competitive_landscape.md` filed; one-paragraph each on PHA / PHIA / SePA / Open Wearables / WHOOP Coach / Hugo.
- *Cost:* 1 day (lifts from §3 of this report).

**W-NOF1-METHOD** doc-only adjunct
- *Acceptance:* `reporting/docs/n_of_1_methodology.md` filed; cites StudyU / Vlaeyen 2024.
- *Cost:* 1 day.

**W-2U-GATE-2** second foreign user
- *Acceptance:* second foreign onboarding session captured; comparison doc filed.
- *Cost:* 2 days.

**v0.2.0 cycle estimate (Path A):** **18-24 days** (W52 + W58D
substrate + 4 doc-only adjuncts). Cycle tier: substantive. **One
schema group** (weekly-review tables + claim-block).

### v0.2.1 (Path A — insight ledger only)

**W53** insight ledger
- *Acceptance:* insight rows persist with provenance; `hai insights` lists; user commit gates promotion to durable insight.
- *Files:* `core/insights/` (new), migration 025.
- *Cost:* 5-7 days.

Plus 1-2 days of doc-fix sweep / freshness work folded in (the cycle
is otherwise small enough that bundling hygiene work is honest).

**v0.2.1 cycle estimate (Path A):** **8-12 days**. Cycle tier:
hardening (single substantive workstream). **One schema group**
(insight ledger tables).

### v0.2.2 (Path A — LLM judge shadow)

**W58 LLM judge** shadow-by-default
- *Acceptance:* `HAI_W58_JUDGE_MODE` flag plumbing; shadow runs log to a separate stream; promotion criterion defined per E-3 (HAI-proposed thresholds).
- *Files:* `core/factuality/judge.py`, `verification/tests/test_judge_shadow.py`, migration 026.
- *Cost:* 4-5 days.

**W-JUDGE-BIAS** bias test panel
- *Folds into W58 judge.* +2 days overhead vs naive promotion criterion.

**v0.2.2 cycle estimate (Path A):** **8-12 days**. Cycle tier:
substantive. **One schema group** (judge log tables).

### v0.2.3 (Path A — judge promotion to blocking + W-30)

**W58 LLM judge** flip from shadow to blocking
- *Acceptance:* bias panel pass per E-3; flag flips; existing tests unchanged.
- *Cost:* 1-2 days.

**W-30** capabilities-manifest schema freeze
- *Acceptance:* manifest schema version pinned; new fields require migration + version bump; existing snapshot tests assert frozen surface.
- *Files:* `verification/tests/test_capabilities.py`, `agent_cli_contract.md` schema field.
- *Cost:* 2 days.

**v0.2.3 cycle estimate (Path A):** **5-8 days**. Cycle tier:
hardening. **No new schema** (flag flip + manifest pin).

**Total Path A v0.2.x effort:** 39-56 days across four cycles.

### Path B fallback estimates (if maintainer chooses single-release CP5)

- v0.2.0 single release: **30-39 days** (substrate + judge shadow +
  W-30; 3 schema groups; 5+ round D14 likely).
- v0.2.0.x or v0.2.1 hardening: **2 days** (W-30 alone).

### v0.3 / v0.4 (futures-only — not yet authored)

**MCP read-surface design** — assumes W-MCP-THREAT artifact exists.
**MCP read-surface ship** — gated by threat-model + provenance proof + scope model.
**No write surface ever.** (Per W57 + CP4.)

---

## 21. Appendix — Citations

### Local citations (file:line; round-1 audit corrected pyproject.toml line and AGENTS.md file-length framing per F-RES-06)

- AGENTS.md:8-12 (project description), :50-59 (load-bearing invariant),
  :89-110 (governance invariants), :112-211 (D1-D15), :293-316 (summary-
  surface sweep pattern). AGENTS.md is 425 lines total per `wc -l`
  (originally cited as `:425 (file length)` which incorrectly suggested
  line-425 content; corrected per F-RES-06).
- README.md:34-38 (hosted-agent runtime exposure caveat — already
  shipped, per F-RES-01), :48 (skill count drift, 15→14), :49 (CLI
  surface).
- ARCHITECTURE.md:65-71 (six domains), :83-90 (audit chain).
- reporting/docs/architecture.md:174 (migrations live; note the doc
  itself says "001-021" while the actual migration set runs through
  022 — minor doc-staleness in the source, not in this report).
  *(Original draft cited `ARCHITECTURE.md:174-199` which is impossible;
  ARCHITECTURE.md is 111 lines per `wc -l`. Corrected per F-RES-R2-06.)*
- ROADMAP.md:13-31 (Now), :34-55 (Next), :57-65 (Later), :79-90
  (stale Dependency Chain — C-DRIFT-02/03/04).
- AUDIT.md:7-31 (v0.1.13 entry).
- CHANGELOG.md:14 (v0.1.13 release date), :179 (W-Vb partial-closure).
- HYPOTHESES.md:8-11 (superseded-roadmap reference), :16-142 (H1-H5).
- pyproject.toml:7 (version 0.1.13). (Original draft cited :3 in
  error; corrected per F-RES-06.)
- reporting/docs/non_goals.md (no clinical, no autonomous plans).
- reporting/docs/architecture.md:115-144 (code-vs-skill).
- reporting/docs/privacy.md:1-177 (privacy commitments).
- reporting/docs/agent_integration.md:119-150 (determinism boundaries).
- reporting/docs/agent_cli_contract.md:1-3, :58 (capabilities surface).
- reporting/plans/strategic_plan_v1.md:140-298 (H1-H5), :326-376
  (validation status), :440-532 (waves), :527-532 (horizon).
- reporting/plans/tactical_plan_v0_1_x.md:31-41 (release table),
  :40 (v0.2.0 row), :441-501 (v0.2.0 detail), :450 (CP5 single-release).
- reporting/plans/eval_strategy/v1.md:58-74 (eval classes), :83-124
  (current coverage), :205-240 (ground-truth methodology), :245-286
  (LLM-judge approach), :290-324 (persona-driven eval).
- reporting/plans/success_framework_v1.md:83-203 (Tier 1 metrics),
  :191-199 (anti-gaming note).
- reporting/plans/risks_and_open_questions.md:57-156 (strategic risks),
  :160-313 (technical risks), :315-421 (operational risks),
  :424-519 (external risks), :522-556 (compounding), :591-701
  (open questions).
- reporting/plans/future_strategy_2026-04-29/reconciliation.md:13
  (verdict), :27-45 (12 agreements), :49-131 (4 disagreements),
  :136-151 (Codex caught), :158-166 (Claude caught), :170-257
  (30-action punch-list).
- reporting/plans/v0_1_13/PLAN.md:60-71 (theme), :129 (scope),
  :585-597 (W-AK contract).
- reporting/plans/v0_1_13/RELEASE_PROOF.md:3 (tier substantive),
  :19-50 (workstream completion), :64-227 (ship gates),
  :289-301 (deferrals).
- src/health_agent_infra/skills/ (14 directories — actual count).
- verification/dogfood/personas/__init__.py:34-37 (12 personas).
- verification/tests/ (177 `test_*.py` files as of this pass).

### External citations (April 2026)

**Source-class note (per F-RES-07):** the original method statement
claimed "primary sources only." That over-claimed; the citations
below mix primary papers and specs with vendor statements, trade
press, security blogs, and a CVE timeline. Source class is
implicitly inferable from URL but a future v0.2.0 doc-fix-sweep
should add explicit `(paper)`, `(spec)`, `(vendor statement)`,
`(trade press)`, `(security advisory)`, `(product documentation)`
labels per Codex F-RES-07.

CALM citation note (per F-RES-05 + F-RES-R2-04): the round-1 draft
attributed CALM to "Park et al. 2024" (search-summary error). Codex
round-2 primary-source check confirms the canonical citation is
**Ye et al. 2025, ICLR — "Justice or Prejudice? Quantifying Biases
in LLM-as-a-Judge"** at OpenReview ID `3GTtZFiajM`. The citation
below has been corrected.

Apple framing note (per F-RES-08): the MDDI link below is **trade
press** about Apple's App Store medical-device-status disclosure
policy, not a regulator-issued mandate. Re-read in that frame.

- **Anatomy of a Personal Health Agent (PHA)**, Heydari et al. 2025 (per Codex round-2 primary-source check) — https://arxiv.org/abs/2508.20148
- **PHIA**, Merrill et al., *Nature Communications 2026* — https://www.nature.com/articles/s41467-025-67922-y
- **PH-LLM**, Cosentino/Belyaeva et al. 2024, *Nature Medicine 2025* — https://arxiv.org/abs/2406.06474
- **SePA**, Sun et al. 2025 — https://arxiv.org/abs/2509.04752
- **Bloom**, Jörke et al. 2025 — https://arxiv.org/abs/2510.05449
- **AgentSpec**, Wang/Poskitt/Sun 2025, ICSE '26 — https://arxiv.org/abs/2503.18666
- **FActScore**, Min et al. 2023, *EMNLP 2023* — https://arxiv.org/abs/2305.14251
- **MedHallu**, Pandit et al. 2025, *EMNLP 2025* — https://arxiv.org/abs/2502.14302
- **HalluLens**, 2025 — https://arxiv.org/html/2504.17550v1
- **No Free Labels**, 2025 — https://arxiv.org/html/2503.05061v1
- **CALM** (Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge), Ye et al. 2025, ICLR — https://openreview.net/forum?id=3GTtZFiajM
- **Rating Roulette**, EMNLP 2025 Findings — https://aclanthology.org/2025.findings-emnlp.1361.pdf
- **JITAI 2025 meta-analysis** (mental health, g=0.15) — https://pmc.ncbi.nlm.nih.gov/articles/PMC12481328/
- **StudyU**, Kaschta et al. 2022, *JMIR* — https://www.jmir.org/2022/7/e35884
- **StudyMe**, Zenner et al. 2022, *Trials* — https://link.springer.com/article/10.1186/s13063-022-06893-7
- **Vlaeyen 2024 SCED practical guide** — https://cris.maastrichtuniversity.nl/ws/portalfiles/portal/206634956/Vlaeyen-2024-Single-case-experimental-designs.pdf
- **MCP Authorization Spec 2025-11-25** — https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- **arXiv 2511.20920 — Securing the Model Context Protocol** — https://arxiv.org/pdf/2511.20920
- **OWASP MCP Top 10** — https://owasp.org/www-project-mcp-top-10/
- **Check Point — CVE-2025-59536 / CVE-2026-21852** — https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/
- **OX Security — MCP architectural RCE disclosure** — https://www.ox.security/blog/the-mother-of-all-ai-supply-chains-critical-systemic-vulnerability-at-the-core-of-the-mcp/
- **OX Security — MCP STDIO technical deep dive** — https://www.ox.security/blog/the-mother-of-all-ai-supply-chains-technical-deep-dive/
- **Authzed timeline of MCP breaches (CVE catalogue)** — https://authzed.com/blog/timeline-mcp-breaches
- **Practical DevSecOps — MCP vulnerabilities 2026** — https://www.practical-devsecops.com/mcp-security-vulnerabilities/
- **Open Wearables (the-momentum)** — https://github.com/the-momentum/open-wearables
- **Open Wearables docs** — https://openwearables.io/docs
- **Open Wearables 0.3 release post** — https://medium.com/@themomentum_ai/open-wearables-0-3-android-support-google-health-connect-samsung-health-9de844e9608c
- **Intervals.icu MCP server** — https://github.com/mvilanova/intervals-mcp-server
- **ActivityWatch** — https://activitywatch.net/
- **HPI** — https://github.com/karlicoss/HPI
- **Fasten Health on-prem** — https://github.com/fastenhealth/fasten-onprem
- **HealthLog** — https://healthlog.dev/
- **Strava API agreement update (Nov 2024, AI/ML prohibition)** — https://press.strava.com/articles/updates-to-stravas-api-agreement
- **Oura API authentication / PAT deprecation** — https://cloud.ouraring.com/docs/authentication
- **WHOOP Coach announcement** — https://www.whoop.com/us/en/thelocker/whoop-unveils-the-new-whoop-coach-powered-by-openai/
- **Apple App Store medical-device-status disclosure policy (MDDI trade press, March 2026)** — https://www.mddionline.com/digital-health/apple-mandates-medical-device-status-for-health-apps-by-2027
- **Composite health scores in consumer wearables (deGruyter 2025)** — https://www.degruyterbrill.com/document/doi/10.1515/teb-2025-0001/html?lang=en
- **JMIR AI 2024 — Explainable AI clinician trust systematic review** — https://ai.jmir.org/2024/1/e53207
- **Tandfonline 2025 — XAI confidence + overreliance** — https://www.tandfonline.com/doi/full/10.1080/10447318.2025.2539458
- **npj Digital Medicine 2025 — Wearable privacy living systematic review** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12167361/
- **Frontiers Digital Health 2025 — wearable AI privacy / GDPR / EU AI Act** — https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2025.1431246/full
- **Wang & Miller 2019 — JITAI meta-analytical review** — https://pubmed.ncbi.nlm.nih.gov/31488002/
- **Nahum-Shani et al. 2017 / 2018 JITAI framework** — https://pmc.ncbi.nlm.nih.gov/articles/PMC5364076/
- **CHA / openCHA**, Abbasian et al. 2024 — https://arxiv.org/abs/2310.02374
- **LLM-as-Judge survey** — https://arxiv.org/abs/2411.15594
- **Scoring Bias in LLM-as-Judge (2025)** — https://arxiv.org/html/2506.22316v1

---

## Caveat

This report was synthesized in a single research session
(2026-05-01) drawing on local file reads, direct grep/line-number
checks, and web research. External citations were spot-checked against
primary or near-primary sources where available; qualitative claims from
marketplace pages, product pages, and security blogs should still be
cross-checked against full text before entering an external pitch deck.
The repo-internal citations are file:line and verifiable. Recommendations
are blunt by design; treat the §6.3 framing-upgrade and the §11 W-30 split
as opinions worth arguing against.

What would change my mind:

- §10 W-2U-GATE: if a foreign user has already done a clean install
  recently and that artifact exists somewhere I missed, this drops to
  P1 doc-only.
- §11 v0.2.0 split: if a real schema coupling that argues against
  Path A (4-release strict-C6 split per reconciliation D1) emerges
  from W52/W53/W58 design, the recommendation flips to Path B
  (single-release per CP5 with new CP overriding C6). Round-1 audit
  confirmed C6 is in tension with CP5; round-2 audit (F-RES-R2-01)
  corrected Path A from 3-release to 4-release for strict-C6
  honouring. The maintainer still must choose Path A vs Path B.
- §10 W-PROV-1: if the existing `recommendation_log` schema already
  carries source-row pointers in some shape I didn't see, this is
  doc-only, not a new type.
- §4 framing upgrade: if Dom doesn't want HAI positioned next to
  AgentSpec for branding/strategic reasons, this is one line of doc
  text, not architecture.

### Note on the research-audit pattern itself (per F-RES-10)

This audit shape — strategic-research artifact + Codex review +
maintainer reconciliation — is being applied for the first time on
this report. **The pattern should remain ad-hoc until at least one
more strategic-research cycle produces evidence that it catches
blocking findings that would otherwise have reached PLAN.md.** Not a
D16 candidate at N=1. R-O-02 (cycle-pattern collapse) and R-O-05
(releases becoming prose-heavy) are both relevant load-bearing risks
against premature codification. See OQ-O for the proposed
retrospective trigger.

### Round-1 outcome

Codex round-1 audit returned REPORT_SOUND_WITH_REVISIONS with 10
findings (9 accepted, 1 partial-accept). Revisions applied in place
2026-05-01.

### Round-2 outcome

Codex round-2 audit returned REPORT_SOUND_WITH_REVISIONS with 7
findings (all accepted). The findings were all residual-revision /
provenance issues from incomplete propagation of round-1 revisions —
none challenged the strategic posture. Round-2 revisions applied in
place 2026-05-01. Maintainer disposition + per-finding rationale at
`codex_research_audit_round_2_response_response.md`.

The audit-chain matches the D14 plan-audit empirical-settling shape
(round 1 ~10, round 2 ~5-7, expected round 3 ~0-2). The research-
audit pattern at N=1 settles like a substantive PLAN audit.

Round-3 launch is at maintainer discretion. Codex round-2 close-out
note: "expected round-3 yield should be 0-2 findings if the
maintainer applies a mechanical sweep rather than hand-editing only
the named lines." A full mechanical pass over §21 is part of the
v0.1.14 doc-fix sweep (W-FRESH-EXT) — closing at round 2 and
deferring the mechanical pass to v0.1.14 is honest if the named
revisions all land cleanly. Per AGENTS.md "Cycle pattern (this
audit's place)" — close at round 2 unless round-3 spot-check warrants
another pass.
