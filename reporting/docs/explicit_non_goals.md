# Explicit Non-Goals

Status: Phase 1 doctrine. Adopted 2026-04-16. Derived from [canonical_doctrine.md](canonical_doctrine.md).

This doc enumerates what Health Lab is **not** doing right now. Each item is deferred, not rejected forever. The purpose is scope discipline: items on this list should not consume time, attention, or repo surface area during the current phase.

## Hard non-goals for this phase

### 1. Many connectors
Only Garmin (passive) and typed manual readiness intake are in scope. No second wearable, no platform sync, no clinic connector, no calendar integration. Connector sprawl before flagship proof is the primary risk to avoid.

### 2. Broad AI health coaching
The system does not produce general wellness advice, lifestyle recommendations outside the flagship's recovery/training envelope, or motivational content.

### 3. Rich UI
No consumer UI, no web dashboard, no mobile app. CLI and file artifacts are sufficient proof surfaces for this phase.

### 4. Deep nutrition system
Nutrition is not an input of the flagship loop. The current runtime does not consume nutrition data at all, and does not emit uncertainty tokens for it.

### 5. Medical-style outputs
No diagnosis, no condition naming, no treatment suggestions, no claims that imply clinical authority.

### 6. MCP expansion
No new MCP servers, tools, or transport layers unless strategically justified by a later phase and explicitly promoted from this non-goal list.

### 7. Large-scale automation
No auto-execution of anything beyond local note / recommendation-log writebacks. No calendar edits, no messages sent, no workout files uploaded.

### 8. Benchmark obsession
No comparative performance claims against other systems or other tools. No leaderboard optimization.

### 9. Broad research branching without flagship progress
Research work continues to live in `research/` but does not count as flagship progress. Research cannot substitute for loop completeness.

### 10. Cosmetic repo refactoring
The eight-bucket repo model is preserved as a workstream organisation layer. Reorganising folders, renaming namespaces, or migrating implementation locations purely for aesthetics is deferred.

### 11. Narrative inflation
Repo-facing language does not describe capability beyond what is concretely implemented. Every major claim maps to an inspectable artifact.

### 12. Multi-user or hosted features
Single local user only. No auth, no tenancy, no hosted runtime.

## Soft non-goals (tolerated only as bounded exploration)

These may exist in the repo as bounded exploratory work but must not be presented as flagship progress:

- the `wger` connector prototype
- Cronometer export bridge
- manual structured gym logging beyond the already-landed Phase 4 prototype
- anything under `research/` or `archive/legacy_product_surfaces/`

## Promotion path

Anything on this list may be promoted to in-scope only via a new dated doctrine doc that supersedes this one. Promotion requires:

1. Flagship proof is complete and legibly public
2. A concrete rationale for why the item makes the flagship proof more real, more inspectable, or more legible
3. A named owner and explicit acceptance criteria

Without that, deferred items stay deferred.

## Related

- [canonical_doctrine.md](canonical_doctrine.md)
- [flagship_loop_spec.md](flagship_loop_spec.md)
- [minimal_policy_rules.md](minimal_policy_rules.md)
