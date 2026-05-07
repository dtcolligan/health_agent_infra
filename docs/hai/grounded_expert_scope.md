# Grounded Expert Scope

The scope / policy contract for the bounded grounded-expert surface. It is a
read-only explanation layer that can answer allowlisted questions about what
terms mean *in this system* and why the runtime would soften, block, or adjust
an action — always with citations, and always from local repository sources.

This doc is load-bearing: it is cited by the expert skill, the
retrieval module, and the expert eval scenarios. A change here is a
change to the prototype's contract.

It pairs with
[`personal_health_agent_positioning.md`](personal_health_agent_positioning.md)
§2 (grounded expert role), [`query_taxonomy.md`](query_taxonomy.md)
§2.5 (grounded topic explanation), and
[`agent_cli_contract.md`](agent_cli_contract.md) for the read-only `hai
research` commands that expose the source registry.

## 1. What the prototype is

A read-only explainer. Given a bounded topic question — for example
*"What does elevated sleep debt mean in this system?"* — the prototype
returns an answer whose every substantive claim is either backed by a
citation from the allowlist below or abstained from.

It is not a chatbot, not a diagnostician, not a recommendation author,
and not a general web-research agent. The runtime's action space stays
exclusively with the runtime analyst and synthesis (see
`personal_health_agent_positioning.md` §2, role 1).

One sentence: *the grounded expert explains; it never acts.*

## 2. Allowed source classes

All three allowlisted classes are **local to this repository**. No
hosted service, no live web fetch, no embedding store.

| Class id | What it covers | Origin |
|---|---|---|
| `internal_state_model` | band definitions, projector semantics, missingness grammar | `docs/hai/state_model_v1.md`, `src/health_agent_infra/domains/*/classify.py` |
| `internal_x_rules` | X-rule triggers and tiers | `docs/hai/x_rules.md`, `src/health_agent_infra/core/synthesis_policy.py` |
| `internal_skill_contract` | what a skill is and is not allowed to do when it composes rationale over a shipped signal (e.g. Garmin body battery) | `src/health_agent_infra/skills/**/SKILL.md` |

Each source record carries a `source_id`, `title`, `source_class`,
`origin_path` (repo-relative), a literal `excerpt` copied from the
origin file, and a set of `topics` it covers. The excerpt exists so a
reader (or a test) can verify that the citation was not fabricated —
the test suite asserts that `excerpt` appears in the live file at
`origin_path`.

Nothing outside this table is quotable by the prototype. A later release
may add new classes (for example `curated_external_guideline`) under
an explicit allowlist and an explicit operator-initiated retrieval
path; v0.1.8 does not.

## 3. Privacy rules

Three load-bearing rules, enforced by the retrieval module:

1. **No user state leaves the machine.** Retrieval runs over the
   packaged source registry in-process. The module opens no socket,
   resolves no external host, and makes no HTTP or DNS request. The
   surface cannot page in a URL or an embedding from a hosted
   service.
2. **No user context travels even locally.** A `RetrievalQuery` carries
   a topic token (e.g. `sleep_debt`) and nothing else. User memory,
   accepted state values, review outcomes, and free-text notes are
   **not** attached to retrieval queries. This rule holds even when the
   skill is invoked with a fully loaded snapshot in the agent's context
   — the *agent* may hold that context, but the *retrieval surface*
   refuses to carry it.
3. **Any off-device send must be explicit and operator-initiated.**
   This phase does not ship such a path. If a later phase adds one, it
   must: be gated behind an environment flag (analogous to
   `HAI_SKILL_HARNESS_LIVE`), print a one-line banner naming the
   destination host + the fields being sent, refuse to auto-fire inside
   `hai daily` / `hai synthesize`, and document the allowlisted
   destinations in this doc before shipping.

The test suite locks rule (2) by asserting that
`RetrievalQuery` rejects payloads flagged as carrying user context
unless an explicit operator-initiated flag is set, and that no such
flag ships today.

## 4. Citation policy

The surface's honesty contract:

1. **Cite or abstain.** Every substantive claim in an answer is either
   backed by at least one source from §2 or explicitly marked as
   abstained. There is no third mode. "Substantive" means: any claim
   about what a term denotes in this system, why a rule fires, what a
   skill is allowed to do, or what a vendor signal reports. It does not
   cover grammatical connective tissue.
2. **Citations are concrete.** A citation carries `source_id`,
   `title`, `origin_path`, and a short excerpt. A reader following the
   citation should land on a file that actually exists and contains the
   quoted excerpt — not on an invented or paraphrased source.
3. **Abstention is first-class.** If retrieval returns no matching
   source (topic off the allowlist, or no source covers it),
   `RetrievalResult.abstain_reason` is set and the skill must surface
   that the system cannot answer, rather than improvising.
4. **No paraphrased authority.** The prototype may summarise an
   excerpt for readability, but it may not attribute a claim to
   `state_model_v1.md` (or any other origin) without the excerpt
   actually appearing there.

## 5. Out-of-scope (non-negotiable)

This surface does *not*, under any circumstance:

1. Mutate a recommendation, a proposal, an X-rule firing, a plan, or
   any row in the runtime's write-surface tables. Zero `INSERT` /
   `UPDATE` / `DELETE` calls from the research path. (Mirrors the
   `hai explain` read-only contract from
   [`explainability.md`](explainability.md) §5.)
2. Run inside `hai daily`, `hai synthesize`, `hai propose`, or policy.
   The research path is never reachable from the synthesis transaction
   or from any deterministic runtime stage. Retrieval is a skill-time
   behaviour, not a runtime-time behaviour.
3. Perform symptom triage or diagnosis. Questions like *"do I have
   overtraining syndrome?"* or *"should I see a doctor about this
   resting heart rate?"* are outside this surface. The prototype
   explicitly refuses such questions and cites
   [`non_goals.md`](non_goals.md) when doing so.
4. Serve open-ended general health-topic questions beyond the
   allowlisted topic set. "What is an ACWR?" is in scope (the system
   uses it explicitly); "what is the best sports drink?" is not.
5. Embed a broad web-search agent. No `WebSearch`, no `WebFetch`, no
   user-directed URL loading inside the research path. If that surface
   is ever needed, it ships under §3 rule 3 and must update this doc
   first.
6. Adopt adaptive memory. The research surface does not learn from
   past queries, does not reweight sources based on user reaction, and
   does not store a per-user preference profile. Learning loops remain
   out-of-cycle (`memory_model.md` §2.2).

## 6. Scope as a test-locked invariant

The scope in this doc is not aspirational. It is locked by focused
tests:

- `verification/tests/test_expert_research.py::test_every_source_origin_exists`
  asserts every shipped source's `origin_path` resolves to a real file
  in the repo.
- `...::test_every_source_excerpt_is_literal` asserts the excerpt
  appears verbatim in the origin file.
- `...::test_retrieval_abstains_on_off_allowlist_topic` asserts that an
  unknown topic returns an abstain result, not a fabricated source.
- `...::test_retrieval_refuses_user_context_payload` asserts the
  privacy guard rejects a query flagged as carrying user context.
- `...::test_retrieval_has_no_network_dependency` asserts the
  retrieval module imports nothing from `urllib`, `requests`, `httpx`,
  or `socket`.

If a later change loosens any of these invariants, the test fails
before the change reaches main — the scope doc is the spec; the tests
are the fence.

## 7. How this extends later

The surface is narrow on purpose. If later releases want to broaden
it, the path is documented so it does not happen quietly:

- **New topic coverage** is cheap: add a `Source` record whose
  `topics` set covers the new token, then add it to
  `ALLOWLISTED_TOPICS`. The existing privacy / citation / abstain
  invariants still hold.
- **A new source class** (e.g. a curated external guideline) requires
  a change to this doc first, then the implementation. It must ship
  with the same excerpt-verification test and must not re-open §5.
- **Off-device retrieval** (a hosted knowledge base, a literature
  lookup) would require §3 rule 3's operator-initiated flag, an
  audit trail of every off-device send, and a scope-doc update that
  enumerates destinations. It is deliberately deferred beyond the current
  bounded local surface.

Any commit that touches the research module without also updating
this doc's §2 / §3 / §5 is, by construction, a scope regression.
