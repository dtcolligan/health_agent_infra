"""Within-family paired capability analysis -- the powered-run PRIMARY.

The estimand is NOT "capable models as a class differ from weak models as a
class" (that comparison is floored by model count and confounded by family
composition). It is the paired, within-family question:

    Within each family, does scaling capability up raise the safe rate in the
    told-but-unenforced cell B?

Each family contributes ONE difference d_f = rate(capable_f) - rate(weak_f) in
cell B. The test is over the family differences. Pairing differences out
between-family variance, so a large, consistent within-family effect reaches
significance with few families -- and every difference is confound-broken (same
family, provider, serving within the pair).

Lineage grouping (honesty guard): families that share a lineage (qwen2.5 and
qwen3 -> "qwen") are correlated, not independent. The report gives BOTH the
pair-level test (each family a unit) and the lineage-collapsed test (same-lineage
families averaged to one difference), so the reader sees the honest range. The
lineage-collapsed test is the conservative primary; the pair-level test is the
optimistic bound.

Primary p-value: an EXACT sign-flip (Fisher) permutation, distribution-free and
assumption-light. Under H0 the sign of each family difference is exchangeable, so
we enumerate all 2**F sign assignments and compute the fraction whose mean meets
or beats the observed. Its floor is 1/2**F when every family agrees in sign, so
it needs F >= 5 to clear 0.05 and F >= 6 to clear ~0.016 on its own -- the exact
reason more (independent) pairs upgrade a parametric-only result to a
permutation-robust one. A parametric paired-t supplement (which uses magnitude
and can clear 0.05 at F=4 when the effect is large) lives in ``paired_t`` behind
the optional-scipy guard.

stdlib + math only in the primary path. Keep it that way.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product
from typing import Any, Callable, Sequence

from .descriptive import RateCI, rate_ci
from .frame import CAPABLE, WEAK, AnalysisFrame


def _round(value: float) -> float:
    return round(value, 12)


@dataclass(frozen=True)
class FamilyDiff:
    """One family's within-family cell-B capability difference."""

    family: str
    lineage: str
    capable: RateCI
    weak: RateCI
    delta: float  # capable.rate - weak.rate

    def as_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "lineage": self.lineage,
            "capable": self.capable.as_dict(),
            "weak": self.weak.as_dict(),
            "delta": _round(self.delta),
        }


def default_lineage_of(family: str) -> str:
    """Collapse a model_family to its lineage (generation-invariant).

    ``qwen2.5`` / ``qwen3`` -> ``qwen``; ``llama3.1`` / ``llama3.3`` -> ``llama``.
    Anything else maps to itself (its own lineage). This is the grouping that
    keeps two same-lineage generation pairs from being counted as independent.
    """

    f = family.lower()
    for prefix in ("qwen", "llama", "mistral", "gemma", "yi", "phi"):
        if f.startswith(prefix):
            return prefix
    return f


def family_differences(
    frame: AnalysisFrame,
    lineage_of: Callable[[str], str] = default_lineage_of,
) -> list[FamilyDiff]:
    """Cell-B within-family (capable - weak) safe-rate difference per family.

    A family enters only if it has BOTH a capable and a weak member with at least
    one cell-B rep each; a family missing a band cannot form a within-family
    difference and is excluded (surfaced by the caller as a coverage gap, never
    silently imputed).
    """

    cell_b = frame.cell("B")
    families = sorted({row.model_family for row in cell_b})
    out: list[FamilyDiff] = []
    for family in families:
        def _in_family(row: Any, _f: str = family) -> bool:
            return bool(row.model_family == _f)

        fam_rows = cell_b.where(_in_family)
        capable = rate_ci(fam_rows.band(CAPABLE))
        weak = rate_ci(fam_rows.band(WEAK))
        if capable.n == 0 or weak.n == 0:
            continue
        out.append(
            FamilyDiff(
                family=family,
                lineage=lineage_of(family),
                capable=capable,
                weak=weak,
                delta=capable.rate - weak.rate,
            )
        )
    return out


def collapse_to_lineage(diffs: Sequence[FamilyDiff]) -> list[tuple[str, float]]:
    """Average same-lineage family deltas into one delta per lineage.

    The conservative unit: two Qwen generation pairs count once. Returns
    ``[(lineage, mean_delta), ...]`` sorted by lineage.
    """

    by_lineage: dict[str, list[float]] = {}
    for d in diffs:
        by_lineage.setdefault(d.lineage, []).append(d.delta)
    return [(lin, sum(v) / len(v)) for lin, v in sorted(by_lineage.items())]


def signflip_permutation_p(deltas: Sequence[float]) -> dict[str, Any]:
    """Exact one-sided sign-flip permutation test for mean(delta) > 0.

    Enumerates all 2**F sign assignments of the observed differences (H0: each
    difference is sign-symmetric about 0). One-sided p = fraction of assignments
    whose mean is >= the observed mean. Also reports the attainable floor
    (1/2**F) so a non-significant result at small F is legible as a power limit,
    not an absence of effect.
    """

    n = len(deltas)
    if n == 0:
        return {"n": 0, "mean_delta": 0.0, "p_one_sided": 1.0, "p_floor": 1.0}
    observed = sum(deltas) / n
    abs_deltas = [abs(d) for d in deltas]
    total = 0
    hits = 0
    for signs in product((-1.0, 1.0), repeat=n):
        mean = sum(s * a for s, a in zip(signs, abs_deltas)) / n
        total += 1
        if mean >= observed - 1e-12:
            hits += 1
    return {
        "n": n,
        "mean_delta": _round(observed),
        "p_one_sided": _round(hits / total),
        "p_floor": _round(1.0 / total),
        "method": "exact_signflip_permutation",
    }


def paired_t(deltas: Sequence[float]) -> dict[str, Any] | None:
    """Parametric one-sided paired-t supplement (uses magnitude; needs scipy).

    Returns None if scipy is unavailable or fewer than 2 differences (t undefined).
    The primary result is the distribution-free permutation; this is the
    magnitude-using supplement that can clear 0.05 at F=4 when the effect is large
    and consistent, at the cost of a normality assumption on the family
    differences -- disclosed, not hidden.
    """

    n = len(deltas)
    if n < 2:
        return None
    try:
        from scipy import stats  # type: ignore
    except ImportError:
        return None
    mean = sum(deltas) / n
    var = sum((d - mean) ** 2 for d in deltas) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0.0:
        # A perfectly consistent effect: t -> inf, p -> 0. Report the degenerate
        # case explicitly rather than dividing by zero.
        return {
            "n": n,
            "mean_delta": _round(mean),
            "sd": 0.0,
            "t": None,
            "df": n - 1,
            "p_one_sided": 0.0 if mean > 0 else 1.0,
            "method": "paired_t_one_sample_degenerate_sd0",
        }
    t = mean / (sd / math.sqrt(n))
    p = float(stats.t.sf(t, df=n - 1))
    return {
        "n": n,
        "mean_delta": _round(mean),
        "sd": _round(sd),
        "t": _round(t),
        "df": n - 1,
        "p_one_sided": _round(p),
        "method": "paired_t_one_sample",
    }


def paired_report(
    frame: AnalysisFrame,
    lineage_of: Callable[[str], str] = default_lineage_of,
) -> dict[str, Any]:
    """The within-family paired PRIMARY report for a powered-run frame.

    Reports the per-family difference table, the pair-level test (optimistic;
    each family a unit) and the lineage-collapsed test (conservative; same-lineage
    families averaged), each with the exact permutation p and its floor, plus the
    paired-t supplement where scipy is present. Deterministic + JSON-serialisable.
    """

    diffs = family_differences(frame, lineage_of)
    pair_deltas = [d.delta for d in diffs]
    lineage_pairs = collapse_to_lineage(diffs)
    lineage_deltas = [d for _lin, d in lineage_pairs]

    return {
        "schema_version": "governed_agent_bench.analysis.paired.v1",
        "n_families": len(diffs),
        "n_lineages": len(lineage_pairs),
        "family_differences": [d.as_dict() for d in diffs],
        "pair_level": {
            "note": "each family a unit (optimistic; same-lineage pairs correlated)",
            "permutation": signflip_permutation_p(pair_deltas),
            "paired_t": paired_t(pair_deltas),
        },
        "lineage_level": {
            "note": "same-lineage families averaged (conservative PRIMARY)",
            "lineage_deltas": [
                {"lineage": lin, "mean_delta": _round(d)} for lin, d in lineage_pairs
            ],
            "permutation": signflip_permutation_p(lineage_deltas),
            "paired_t": paired_t(lineage_deltas),
        },
    }


__all__ = [
    "FamilyDiff",
    "collapse_to_lineage",
    "default_lineage_of",
    "family_differences",
    "paired_report",
    "paired_t",
    "signflip_permutation_p",
]
