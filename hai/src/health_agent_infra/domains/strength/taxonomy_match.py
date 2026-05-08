"""Code-owned taxonomy match + search for the strength domain.

Phase 4 step 4. All exercise-name resolution logic the intake CLI and
the strength-intake narration skill rely on is **here**, not in
markdown. The skill surface may only *describe when to ask the user
for clarification*; it may not decide which taxonomy entry a name
matches.

Two public entry points:

  - :func:`match_exercise_name` — deterministic single-name match.
    Returns an :class:`ExerciseMatch` with an explicit
    ``confidence`` tier: ``exact`` (canonical name), ``alias``
    (alias hit), ``ambiguous`` (multiple taxonomy rows expose the
    same alias key), ``no_match``.
  - :func:`search_exercises` — ranked top-N search for agent
    disambiguation. Returns a list of :class:`SearchHit` objects
    ordered by descending relevance score. Used by
    ``hai exercise search`` and by the strength-intake skill when
    it needs to present candidates to the user.

The ranking function is deliberately simple and fully deterministic.
Substring and token-overlap heuristics — no fuzzy distance, no ML.
Ties break on ``canonical_name`` lexicographic order so the output
is stable across runs and platforms.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Optional

from health_agent_infra.core.state.projectors.strength import (
    TaxonomyEntry,
    _build_index_from_conn,
    _norm,
    _split_pipe,
)


MatchConfidence = str  # "exact" | "alias" | "ambiguous" | "no_match"


@dataclass(frozen=True)
class ExerciseMatch:
    """Outcome of resolving one free-text name against the taxonomy.

    When ``confidence`` is ``exact`` or ``alias`` the caller can
    safely stamp ``exercise_id`` on ``gym_set``. When ``confidence``
    is ``ambiguous`` or ``no_match`` the agent must ask the user to
    disambiguate; stamping an arbitrary pick would corrupt downstream
    aggregates.
    """

    input_name: str
    exercise_id: Optional[str]
    canonical_name: Optional[str]
    confidence: MatchConfidence
    alternatives: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SearchHit:
    """One ranked row for ``hai exercise search``."""

    exercise_id: str
    canonical_name: str
    aliases: tuple[str, ...]
    primary_muscle_group: str
    secondary_muscle_groups: tuple[str, ...]
    category: str
    equipment: str
    score: int
    match_reason: str   # e.g. "exact_canonical" | "substring_alias" | "token_overlap"


# ---------------------------------------------------------------------------
# Index loading — shared with the projector so one taxonomy pass
# feeds both name-resolution and search.
# ---------------------------------------------------------------------------


def load_taxonomy_with_aliases(
    conn: sqlite3.Connection,
) -> tuple[dict[str, TaxonomyEntry], dict[str, tuple[str, ...]], dict[str, str]]:
    """Return (taxonomy_by_id, aliases_by_id, resolver_index).

    ``resolver_index[norm_token] = exercise_id`` mirrors the projector's
    resolver. ``aliases_by_id[exercise_id]`` is the tuple of raw
    aliases for that row (useful for search display).
    """

    taxonomy, resolver = _build_index_from_conn(conn)
    aliases_by_id: dict[str, tuple[str, ...]] = {}
    for row in conn.execute(
        "SELECT exercise_id, aliases FROM exercise_taxonomy"
    ).fetchall():
        aliases_by_id[row["exercise_id"]] = _split_pipe(row["aliases"])
    return taxonomy, aliases_by_id, resolver


# ---------------------------------------------------------------------------
# Single-name resolution — deterministic, explicit confidence tiers.
# ---------------------------------------------------------------------------


def match_exercise_name(
    name: str,
    *,
    taxonomy: dict[str, TaxonomyEntry],
    aliases_by_id: dict[str, tuple[str, ...]],
    resolver: dict[str, str],
) -> ExerciseMatch:
    """Resolve one free-text exercise name into a typed match verdict.

    Decision order:

      1. Case-folded exact canonical match → confidence='exact'.
      2. Case-folded exact alias match → confidence='alias'. If
         multiple taxonomy entries list the same alias the resolver
         returned the first by ``exercise_id`` sort order; we detect
         the collision and downgrade to ``ambiguous`` with every
         colliding ``exercise_id`` surfaced as ``alternatives``.
      3. Miss → confidence='no_match'.
    """

    if not name or not name.strip():
        return ExerciseMatch(
            input_name=name, exercise_id=None, canonical_name=None,
            confidence="no_match",
        )

    key = _norm(name)

    # 1. Exact canonical match?
    for entry in taxonomy.values():
        if _norm(entry.canonical_name) == key:
            return ExerciseMatch(
                input_name=name,
                exercise_id=entry.exercise_id,
                canonical_name=entry.canonical_name,
                confidence="exact",
            )

    # 2. Alias hit — scan every entry to detect collisions.
    alias_hits: list[str] = []
    for eid, aliases in aliases_by_id.items():
        for alias in aliases:
            if _norm(alias) == key:
                alias_hits.append(eid)
                break

    if len(alias_hits) == 1:
        eid = alias_hits[0]
        return ExerciseMatch(
            input_name=name,
            exercise_id=eid,
            canonical_name=taxonomy[eid].canonical_name,
            confidence="alias",
        )

    if len(alias_hits) > 1:
        alts = tuple(sorted(alias_hits))
        primary = alts[0]
        return ExerciseMatch(
            input_name=name,
            exercise_id=primary,
            canonical_name=taxonomy[primary].canonical_name,
            confidence="ambiguous",
            alternatives=alts,
        )

    # 3. Final check — resolver (canonical + alias lookup in one pass)
    #    may have handed us a match whose origin we can't classify here
    #    (shouldn't happen given the explicit canonical/alias scan above,
    #    but we respect the resolver as the single source of truth for
    #    successful lookups).
    resolved = resolver.get(key)
    if resolved is not None:
        return ExerciseMatch(
            input_name=name,
            exercise_id=resolved,
            canonical_name=taxonomy[resolved].canonical_name,
            confidence="alias",  # conservative default — we only get here
                                  # if canonical scan missed but resolver hit.
        )

    return ExerciseMatch(
        input_name=name, exercise_id=None, canonical_name=None,
        confidence="no_match",
    )


# ---------------------------------------------------------------------------
# Ranked search — for hai exercise search and narration disambiguation.
# ---------------------------------------------------------------------------

# Scoring weights. Kept in code (not config) because they set the
# interpretation of the search surface; the agent should not be
# tunable around them.
_SCORE_EXACT_CANONICAL = 100
_SCORE_EXACT_ALIAS = 80
_SCORE_SUBSTRING_CANONICAL = 30
_SCORE_SUBSTRING_ALIAS = 20
_SCORE_TOKEN_OVERLAP = 5  # per matching token


def _tokens(s: str) -> set[str]:
    return {t for t in _norm(s).replace("-", " ").split() if t}


def _score_entry(
    query: str,
    entry: TaxonomyEntry,
    aliases: tuple[str, ...],
) -> tuple[int, str]:
    """Return ``(score, best_match_reason)`` for one entry against query."""

    q = _norm(query)
    qset = _tokens(query)
    if not q:
        return 0, "empty_query"

    canonical_norm = _norm(entry.canonical_name)
    alias_norms = [_norm(a) for a in aliases]

    # Exact matches dominate.
    if canonical_norm == q:
        return _SCORE_EXACT_CANONICAL, "exact_canonical"
    if q in alias_norms:
        return _SCORE_EXACT_ALIAS, "exact_alias"

    score = 0
    reason = "no_match"

    # Substring matches — bidirectional so "squat" matches "Back Squat"
    # and "bss" matches the "bss" alias token directly.
    if q in canonical_norm or canonical_norm in q:
        score += _SCORE_SUBSTRING_CANONICAL
        reason = "substring_canonical"
    else:
        for alias in alias_norms:
            if q in alias or alias in q:
                score += _SCORE_SUBSTRING_ALIAS
                reason = "substring_alias"
                break

    # Token overlap — "bench db" should find "Dumbbell Bench Press"
    # via the canonical-name token set.
    canonical_tokens = _tokens(entry.canonical_name)
    alias_tokens: set[str] = set()
    for alias in aliases:
        alias_tokens |= _tokens(alias)
    overlap = len(qset & (canonical_tokens | alias_tokens))
    if overlap > 0:
        score += overlap * _SCORE_TOKEN_OVERLAP
        if reason == "no_match":
            reason = "token_overlap"

    return score, reason


def search_exercises(
    query: str,
    *,
    conn: sqlite3.Connection,
    limit: int = 10,
) -> list[SearchHit]:
    """Return the top-``limit`` taxonomy hits for ``query``, ranked.

    Empty / whitespace-only queries return an empty list. Ties break
    on ``canonical_name`` lexicographic order so the CLI output is
    byte-stable across runs and platforms.
    """

    if not query or not query.strip():
        return []

    taxonomy, aliases_by_id, _ = load_taxonomy_with_aliases(conn)

    scored: list[tuple[int, str, TaxonomyEntry, str]] = []
    for eid, entry in taxonomy.items():
        aliases = aliases_by_id.get(eid, ())
        score, reason = _score_entry(query, entry, aliases)
        if score > 0:
            scored.append((score, entry.canonical_name, entry, reason))

    # Sort by score desc, canonical asc for deterministic output.
    scored.sort(key=lambda t: (-t[0], t[1]))

    hits: list[SearchHit] = []
    for score, _cn, entry, reason in scored[:limit]:
        hits.append(
            SearchHit(
                exercise_id=entry.exercise_id,
                canonical_name=entry.canonical_name,
                aliases=aliases_by_id.get(entry.exercise_id, ()),
                primary_muscle_group=entry.primary_muscle_group,
                secondary_muscle_groups=entry.secondary_muscle_groups,
                category=entry.category,
                equipment=entry.equipment,
                score=score,
                match_reason=reason,
            )
        )
    return hits
