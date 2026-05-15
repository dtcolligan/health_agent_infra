# Founder Doctrine

Status: founder one-page doctrine draft. Written 2026-04-17 from founder interview plus project context. Intended to sharpen project identity, flagship scope, and success criteria.

## Identity

Health Lab is a **local-first runtime and contract layer for agent-mediated personal health work over user-owned data**.

It is not:
- a chatbot
- a dashboard
- a generic health coach
- a clinical decision engine
- a hosted multi-user app

Its job is to let an agent:
- pull health evidence from sources the user already controls
- maintain a longitudinal health state with explicit provenance and missingness
- interpret that state safely
- emit bounded recommendations
- write back recommendations and outcomes
- improve future tailoring through review history

The product is not "AI answers health questions."
The product is **stateful, reviewable agent behavior over personal health data**.

## Core Thesis

The missing layer in health AI is not raw intelligence. It is the runtime that makes intelligence trustworthy enough to matter.

Health Lab creates value by combining:
- deterministic evidence handling
- explicit health-state maintenance
- bounded agent interpretation
- policy-constrained recommendations
- writeback and review loops

Personalization should happen primarily at the **state-to-action layer**, not only in chat.

## Flagship V1

Flagship v1 is:

**full personal health state maintenance with one narrow primary action loop**

The state should span, at minimum:
- sleep
- nutrition
- running
- gym / resistance training
- recovery
- stress / context
- acute and chronic load
- goals
- recommendation history
- review outcomes

The first user-visible action the system must do well is:

**recommend today's training intensity, summarize what happened today, and say what to do tomorrow**

This is the right first wedge because it is:
- naturally longitudinal
- easy to review
- personally meaningful
- lower-risk than broader health advice
- strong enough to prove the state-and-action architecture

## Architecture

The preferred control-plane architecture is:

`PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW`

Interpretation and much of recommendation shaping can live in agent skills.
But deterministic code must still own:
- evidence acquisition
- canonical state shape
- provenance
- missingness accounting
- merge / writeback validation
- bounded persistence

The agent may interpret state and propose state updates.
The runtime must still decide what state is accepted and persisted.

## Connector Doctrine

The long-term product requires the user to authenticate once and let the agent pull data automatically.

But flagship proof should not be blocked on every source having a perfect live connector on day one.

What must be true in v1:
- the canonical state model covers the full target domains
- at least one real connector path works end to end
- the agent can maintain state across domains
- manual or structured fallback paths are acceptable where automation is not finished yet

Connector breadth is not the flagship. Trustworthy state maintenance is.

## Boundaries

Hard constraints:
- local-first
- no clinical claims
- no diagnosis engine
- no UI-first productization
- no hosted multi-user platform
- no connector sprawl before the flagship loop is real
- no overclaiming beyond what code, artifacts, and tests prove

The project should emulate the systems discipline of products like Garmin, Strava, Heavy, and Whoop, but expose that discipline for open agent workflows rather than clone their apps.

## Success Standard

This project succeeds when all of the following are true:
- it works end to end for the founder in real life
- it maintains a trustworthy, inspectable health state over multiple domains
- its recommendation loop is clearly better than generic chat-layer coaching
- recommendation outcomes are tracked and influence future tailoring
- the safety boundary is real in code, not only in prose
- the install story works for an outside builder
- the repo is legible enough that an outsider can see the system is serious

This is both a technical goal and a signaling goal.
The artifact should feel narrow, real, and unusually well-architected.

## Main Failure Modes

The scariest failures are:
- incorrect or stale state
- recommendations grounded in the wrong state
- fake confidence from prompts without code-enforced boundaries
- brittle connectors that make the system unusable
- repository language that outruns implementation reality

The central rule is:

**state integrity matters more than recommendation cleverness**

## Near-Term Milestones

1. Make the safety and recommendation boundary real in code.
2. Make the doctrine and docs match the live architecture.
3. Add the missing manual-readiness and state-maintenance control surfaces.
4. Make fresh install and skills packaging work in a clean environment.
5. Regenerate a flagship proof bundle that reflects the current agent-driven architecture.

## Operating Rule

Do not cut ambition.
Do cut what counts as the first proof.

Health Lab should aim for:
- **broad state**
- **narrow action**

That is how the project becomes undeniable without becoming vague.
