# CP-2U-GATE-FIRST — Insert W-2U-GATE as the first v0.1.14 workstream

**Cycle:** v0.1.14 (PLAN authoring upcoming).
**Author:** Claude (delegated by maintainer).
**Codex verdict:** *not yet authored* (CP draft, pre-acceptance).
**Application timing:** at v0.1.14 PLAN.md authoring — inserts a new
workstream as §2.A of the new PLAN; tactical_plan_v0_1_x.md §5.1
gains a new row; strategic_plan_v1.md gains a §11 footnote on
second-user-readiness as a cycle-gating concern.
**Source:** Strategic-research report 2026-05-01 §5 P0-1, §10, §12.
Codex round-1 audit confirmed the recommendation; round-2 audit did
not flag.

---

## Rationale

v0.1.13 W-AA / W-AC / W-AF shipped the test surface for onboarding
(`hai init --guided` 7-step orchestrator, README quickstart smoke
test, acceptance matrix contract test). They have not been
empirically validated by a non-maintainer running a clean `pipx
install` on their own machine.

"Trusted first value" is the v0.1.13 theme name (W-A1C7 per
`reporting/plans/v0_1_13/PLAN.md:60-71`). Until a foreign user
reaches `synthesized` state without the maintainer's hands on the
keyboard, the theme is unproven. Every later workstream (W52 weekly
review, W58 factuality gate, MCP read surface) inherits the
foreign-machine-onboarding risk.

**W-2U-GATE ranks above every other v0.1.14 workstream** because if
it surfaces a structural blocker (e.g., the foreign user can't get
past `hai init --guided` step 4), v0.1.14 reshapes around the fix;
downstream work moves to v0.1.15 without prejudice. Sequencing it
last would mean every other v0.1.14 W-id ships against an unproven
substrate.

This is not a settled-decision change. It is a sequencing convention
for v0.1.14. A formal CP authoring is appropriate because it sets
precedent for future cycles ("when a substrate workstream surfaces,
sequence it before feature workstreams").

## Proposed delta — v0.1.14 PLAN.md §2 ordering

**v0.1.14 PLAN.md §2 should open with:**

```
### §2.A — W-2U-GATE: foreign-machine onboarding empirical proof

**Why first.** v0.1.13 shipped the test surface for "trusted first
value" (W-AA, W-AF, W-A1C7). This workstream produces the empirical
proof that the test surface holds against a non-maintainer user.
If it surfaces a structural blocker, the cycle reshapes; downstream
work moves to v0.1.15.

**Workstream:**
- One recorded foreign-machine onboarding session by a non-
  maintainer.
- Capture: terminal recording, time-to-`synthesized`, every place
  the user paused, every place they had to ask the maintainer.
- Output artifact:
  `reporting/docs/second_user_onboarding_2026-XX.md` with verbatim
  feedback + remediation plan.

**Acceptance:**
- One full session reaches `synthesized` without maintainer
  intervention.
- Remediation list filed; each item triaged P0/P1/P2.
- If P0 items surface, v0.1.14 reshapes around them.

**Cost:** 2-3 days (mostly coordination + writing).

**Sequencing.** §2.B onwards (W-AH, W-AI, W-AJ, W-AL, W-AM, W-AN
plus inherited W-29, W-Vb-3, W-DOMAIN-SYNC) proceed only after
W-2U-GATE either (a) closes clean or (b) generates a P0 remediation
that is folded into the cycle.
```

## Proposed delta — strategic_plan_v1.md (§11 or appropriate section)

Add a one-paragraph note that "second-user readiness" is a cycle-
gating concern across v0.1.x:

```
Substrate cycles (v0.1.x) gate on second-user empirical proof
before feature cycles. v0.1.14 sequences W-2U-GATE first; future
substrate cycles follow the precedent unless explicitly carved out.
```

## Proposed delta — tactical_plan_v0_1_x.md §5.1

Add a row at the top of v0.1.14 in-scope:

```
| **W-2U-GATE** | Foreign-machine onboarding empirical proof | 2-3 days |
```

with a note that W-2U-GATE precedes all other v0.1.14 W-ids in
sequencing.

## Affected files

- `reporting/plans/v0_1_14/PLAN.md` (new at v0.1.14 PLAN authoring)
- `reporting/plans/strategic_plan_v1.md` (one-paragraph addition)
- `reporting/plans/tactical_plan_v0_1_x.md` §5.1 (new row + note)

## Dependent cycles

- v0.1.14 — direct application.
- v0.2.0+ — sequencing precedent inherited if substrate cycles
  re-appear.
- W-2U-GATE-2 (second foreign user) sequences in v0.2.0 per
  strategic-research §12.

## Acceptance gate

- `accepted`: v0.1.14 PLAN.md §2.A is W-2U-GATE; downstream W-ids
  follow.
- `accepted-with-revisions`: sequencing intact, scope or acceptance
  criteria revised. The "first workstream" placement is the
  load-bearing claim; if a CP-revision moves W-2U-GATE later, the
  cycle's substrate-vs-feature ordering breaks.
- `rejected`: v0.1.14 PLAN sequences workstreams by tactical-plan
  default (no foreign-user gate); CP archived; W-2U-GATE retained
  as a v0.1.14 W-id but not the first one.

## Round-N codex verdict

*pending — CP not yet submitted to Codex review.*
