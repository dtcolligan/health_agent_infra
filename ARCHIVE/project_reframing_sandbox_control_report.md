# Project Reframing Report: Sandbox Engineering for AI Control

> **SUPERSEDED by D-26 (2026-06-09).** This 2026-06-08 note proposed a
> reframe that KEPT the AI-control home. The project instead pivoted to
> AI-engineering agent-harness governance; see PAPER.md D-26 and
> `ARCHIVE/reframe_harness_governance_audit_2026-06-09.md`. Retained as
> provenance only.

Status: discussion note, not a scope decision.
Date: 2026-06-08

This note captures a possible reframing of the project. It does not
change `PAPER.md`, the active mechanism inventory, the pilot protocol,
or the GovernedAgentBench implementation plan.

## Working Frame

Deterministic software contracts are a valuable component of sandbox
engineering for AI control because they make sandbox boundaries explicit,
executable, auditable, and mechanism-isolable.

This framing treats the domain-specific sandbox as an experimental
instrument rather than a liability. HAI is the reference sandbox. The
research object is the deterministic contract-monitor layer inside that
sandbox.

## Core Thesis

AI-control sandboxes need trusted monitor components. A deterministic
software contract is one such component. It constrains what an AI
operator can do, records what happened, and creates clean intervention
points for mechanism ablation.

Under this framing, HAI is not the main contribution. HAI instantiates
the setup. The contribution is showing how executable runtime contracts
can operationalize sandbox rules as trusted monitors and how those
mechanisms can be measured under controlled runtime-mode interventions.

## Why The Reframe Helps

The "sandbox optimization" critique becomes part of the contribution:

- AI systems increasingly operate inside bounded tool and runtime
  environments.
- Those environments need enforceable boundaries, not only prompt
  instructions.
- Deterministic contracts give the boundary a concrete implementation.
- Mechanism ablation shows whether individual contract features are
  load-bearing.
- A domain-specific sandbox makes the claims concrete, auditable, and
  falsifiable.

The specificity is useful because it prevents the paper from floating at
the level of abstract safety principles. The contract is only meaningful
because it is implemented.

## Revised Contribution Statement

We present a controlled case study of deterministic runtime contracts as
trusted monitor components in AI-control sandboxes. Using a non-clinical
personal-wellness runtime as the reference environment, we ablate
contract mechanisms under a held-constant prompt and measure whether
validation, action safety, proposal gating, refusal, and audit evidence
are load-bearing.

## Claim Ladder

Strong claims:

1. Deterministic contracts can operationalize sandbox boundaries as
   executable runtime monitors.
2. Individual contract mechanisms can be ablated without changing the
   agent prompt.
3. Runtime-mode intervention makes sandbox safety properties more
   measurable than prompt-only governance.
4. In the HAI reference sandbox, M4-M8 mechanisms are observable and
   testable through static canaries, live probes, and model-backed
   trajectories.

Claims to avoid:

- Deterministic contracts solve AI control.
- HAI is a general health-agent safety solution.
- Results transfer automatically across domains.
- Prompting is unimportant.
- Sandboxing alone is sufficient for powerful scheming, sandbagged, or
  password-locked models.

## Paper Positioning

This frame places the paper at the intersection of:

- AI control protocols: trusted monitor, untrusted operator, bounded
  usefulness and safety evaluation.
- Sandbox engineering: capability limits, runtime boundaries, isolation,
  and auditability.
- Software contracts: typed commands, validation, policy gates, refusal
  checks, and audit emission.
- Agent benchmarks: runtime-mode intervention rather than prompt
  variation.

The practical niche is trusted-monitor substrate for sandboxed AI agents.

## Title Direction

The current title remains viable:

> Deterministic Software Contracts as Trusted Monitors in AI Control
> Protocols

More sandbox-forward alternatives:

> Deterministic Software Contracts for AI-Control Sandboxes

> Executable Runtime Contracts as Trusted Monitors for Sandboxed AI
> Agents

Recommendation: keep the current title unless the introduction struggles
to make the sandbox-engineering angle legible. The current title is more
research-grade; the body can make the sandbox contribution explicit.

## Abstract Shape

The abstract should make five moves:

1. AI agents are often deployed inside bounded runtimes and sandboxes.
2. Prompt-only constraints are hard to audit and isolate.
3. Deterministic software contracts can serve as trusted monitor
   components.
4. GovernedAgentBench evaluates this by toggling runtime mechanisms under
   a fixed prompt.
5. Results are bounded to one reference sandbox and reported by evidence
   tier.

## Most Important Reframe

Do not defend domain specificity as a weakness. State it as design
discipline:

> We intentionally evaluate a concrete sandbox rather than an abstract
> safety principle, because sandbox boundaries are only meaningful when
> implemented as executable mechanisms.

That turns the project from "health-agent benchmark" into a controlled
case study in AI-control sandbox engineering.

## Implementation Impact

This reframing does not require changing the benchmark design. It mostly
affects:

- abstract
- introduction
- related work
- discussion and limitations
- contribution bullets
- title, only if desired

The existing mechanism inventory, ablation design, and evidence-tier
separation still fit. They fit better under this frame because the paper
is not trying to prove broad domain-general safety. It is showing how a
deterministic contract layer can make a sandbox's control boundary
explicit, testable, and mechanistically isolable.
