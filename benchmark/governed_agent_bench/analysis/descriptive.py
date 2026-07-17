"""Descriptive primary analysis (D4=A): per-cell/per-band safe rates + exact CIs.

The powered run's primary readout is descriptive, not a single p-value: pooled
safe counts per cell and per capability band, each with an exact Clopper-Pearson
interval, and the headline cross-band contrast inside cell B with a
boundary-robust Newcombe interval on the difference.

Dependency policy: no scipy. The exact per-proportion interval reuses the
released, validated ``results.exact_tests.clopper_pearson`` (incomplete-beta
bisection). The between-band difference interval uses Wilson + Newcombe method
10 -- the same construction the frozen ``cell_contrasts`` module uses for its
contrast CIs -- reimplemented here (small, and cross-checked against that module
in the tests) so this package does not depend on a private name in the frozen
paper-v1 surface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from governed_agent_bench.results.exact_tests import clopper_pearson

from .frame import CAPABLE, CELL_ORDER, WEAK, AnalysisFrame

# Two-sided 95% normal quantile, matching cell_contrasts._Z95 so the Newcombe
# intervals here agree with the frozen module bit-for-bit.
_Z95 = 1.959963984540054


def _round(value: float) -> float:
    return round(value, 12)


def wilson_interval(k: int, n: int, z: float = _Z95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion k/n (as fractions)."""

    if n == 0:
        return (0.0, 1.0)
    phat = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (phat + z2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(phat * (1 - phat) / n + z2 / (4 * n * n))
    return (max(0.0, center - half), min(1.0, center + half))


def newcombe_diff_ci(
    k1: int, n1: int, k2: int, n2: int, z: float = _Z95
) -> tuple[float, float]:
    """Newcombe (method 10) CI for the difference p1 - p2 (as fractions).

    Boundary-robust where a Wald interval would run off [0, 1] or collapse to
    zero width at a saturated cell (every observed rate in {0, 1}), which is the
    exact regime the mutation-gate cells produce.
    """

    if n1 == 0 or n2 == 0:
        raise ValueError("newcombe_diff_ci requires n1 > 0 and n2 > 0")
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson_interval(k1, n1, z)
    l2, u2 = wilson_interval(k2, n2, z)
    diff = p1 - p2
    lower = diff - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = diff + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return (lower, upper)


@dataclass(frozen=True)
class RateCI:
    """A safe-rate estimate with an exact Clopper-Pearson interval."""

    k: int  # safe reps
    n: int  # total reps
    rate: float  # k / n (None-safe: 0.0 when n == 0)
    ci95_low: float
    ci95_high: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "k": self.k,
            "n": self.n,
            "rate": _round(self.rate),
            "ci95": [_round(self.ci95_low), _round(self.ci95_high)],
            "ci_method": "clopper_pearson",
        }


@dataclass(frozen=True)
class Contrast:
    """A difference of two safe rates (minuend - subtrahend) with Newcombe CI."""

    label: str
    minuend: RateCI
    subtrahend: RateCI
    delta: float  # minuend.rate - subtrahend.rate
    ci95_low: float
    ci95_high: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "minuend": self.minuend.as_dict(),
            "subtrahend": self.subtrahend.as_dict(),
            "delta": _round(self.delta),
            "ci95": [_round(self.ci95_low), _round(self.ci95_high)],
            "ci_method": "newcombe_method10",
            "min_cell_n": min(self.minuend.n, self.subtrahend.n),
        }


def rate_ci(frame: AnalysisFrame, alpha: float = 0.05) -> RateCI:
    """Safe rate + Clopper-Pearson interval over every row in ``frame``."""

    k, n = frame.kn()
    if n == 0:
        return RateCI(k=0, n=0, rate=0.0, ci95_low=0.0, ci95_high=1.0)
    lo, hi = clopper_pearson(k, n, alpha)
    return RateCI(k=k, n=n, rate=k / n, ci95_low=lo, ci95_high=hi)


def contrast(minuend: RateCI, subtrahend: RateCI, label: str) -> Contrast:
    """Difference minuend - subtrahend with a Newcombe method-10 interval.

    Both cells must be non-empty; an empty cell has no rate to contrast and the
    caller should surface that as a coverage gap rather than a delta.
    """

    if minuend.n == 0 or subtrahend.n == 0:
        raise ValueError(
            f"contrast {label!r} needs both cells non-empty "
            f"(got n={minuend.n}, {subtrahend.n})"
        )
    lo, hi = newcombe_diff_ci(minuend.k, minuend.n, subtrahend.k, subtrahend.n)
    return Contrast(
        label=label,
        minuend=minuend,
        subtrahend=subtrahend,
        delta=minuend.rate - subtrahend.rate,
        ci95_low=lo,
        ci95_high=hi,
    )


def cellB_band_contrast(frame: AnalysisFrame) -> Contrast:
    """The headline: P(safe | cell B, capable) - P(safe | cell B, weak).

    Positive delta => capable models self-enforce the boundary in the told-and-
    unenforced cell where weak models do not, i.e. specification substitutes for
    enforcement for capable models but weak models still need the runtime. This
    is the "substitution is capability-gated" quantity.
    """

    cell_b = frame.cell("B")
    capable = rate_ci(cell_b.band(CAPABLE))
    weak = rate_ci(cell_b.band(WEAK))
    return contrast(capable, weak, label="cellB_capable_minus_weak")


def salience_breakdown(frame: AnalysisFrame) -> list[dict[str, Any]]:
    """The cell-B band contrast at each salience level, ascending.

    A capability x salience interaction shows up here as the band contrast
    changing with salience (e.g. the capable/weak gap shrinking as the boundary
    cue becomes more explicit). Levels where either band is empty are reported
    with the available per-band rates and ``contrast: None`` rather than dropped.
    """

    cell_b = frame.cell("B")
    out: list[dict[str, Any]] = []
    for level in cell_b.salience_levels():
        at_level = cell_b.salience(level)
        capable = rate_ci(at_level.band(CAPABLE))
        weak = rate_ci(at_level.band(WEAK))
        entry: dict[str, Any] = {
            "salience": level,
            "capable": capable.as_dict(),
            "weak": weak.as_dict(),
        }
        if capable.n > 0 and weak.n > 0:
            entry["contrast"] = contrast(
                capable, weak, label=f"cellB_capable_minus_weak@salience={level}"
            ).as_dict()
        else:
            entry["contrast"] = None
        out.append(entry)
    return out


def descriptive_report(frame: AnalysisFrame) -> dict[str, Any]:
    """Full deterministic descriptive report for one powered-run frame.

    Contains, for the reader to audit directly: per-cell overall rates, per-cell
    per-band rates (all with Clopper-Pearson intervals), the headline cell-B
    band contrast, and the salience breakdown. JSON-serialisable and stable
    (sorted keys, rounded floats) for artifact diffing.
    """

    cells: dict[str, Any] = {}
    for name in CELL_ORDER:
        cell = frame.cell(name)
        cells[name] = {
            "overall": rate_ci(cell).as_dict(),
            "capable": rate_ci(cell.band(CAPABLE)).as_dict(),
            "weak": rate_ci(cell.band(WEAK)).as_dict(),
        }
    return {
        "schema_version": "governed_agent_bench.analysis.descriptive.v1",
        "n_rows": len(frame),
        "counts_by_cell": frame.counts_by_cell(),
        "cells": cells,
        "headline_cellB_band_contrast": cellB_band_contrast(frame).as_dict()
        if frame.cell("B").band(CAPABLE).kn()[1] > 0
        and frame.cell("B").band(WEAK).kn()[1] > 0
        else None,
        "salience_breakdown": salience_breakdown(frame),
    }


__all__ = [
    "Contrast",
    "RateCI",
    "cellB_band_contrast",
    "contrast",
    "descriptive_report",
    "newcombe_diff_ci",
    "rate_ci",
    "salience_breakdown",
    "wilson_interval",
]
