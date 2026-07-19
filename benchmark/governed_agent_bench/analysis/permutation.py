"""Permutation tests: the primary inference for the powered run (no scipy).

Two pre-registered tests, both restricted to cell B (told + off), where the
capability signal lives:

H1 (primary) -- the capability gate. Null: the ``capable`` / ``weak`` label is
exchangeable across cell-B reps (no capability effect on the told-and-unenforced
safe rate). Statistic: the band difference in safe rate, capable - weak. A large
positive value is the "capable models self-enforce where weak models need the
runtime" effect. Label permutation over all cell-B reps -> exact-style p.

H2 (key secondary) -- does the gate move with boundary salience? Null: within
each band, salience is exchangeable (no salience effect and no capability x
salience interaction). Statistic: a difference-in-differences / gap-trend that is
INVARIANT to a pure salience main effect -- a main effect shifts both bands
equally and cancels in the per-level gap -- so the test has power only against
the interaction. Permuting salience WITHIN band preserves the band main effect
(which we are not testing) and nulls exactly the salience/interaction structure.

p-values use the add-the-observed-table convention p = (1 + #{as-extreme}) /
(n_perm + 1), which is valid (never zero) for any finite n_perm. Randomness is a
seeded ``numpy.random.default_rng`` so a given (frame, seed, n_perm) is exactly
reproducible -- required for a pre-registered analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .frame import CAPABLE, WEAK, AnalysisFrame


def _round(value: float) -> float:
    return round(value, 12)


@dataclass(frozen=True)
class PermutationResult:
    """Outcome of one permutation test."""

    statistic: str
    observed: float
    n_perm: int
    seed: int
    p_two_sided: float
    p_one_sided_greater: float
    null_mean: float
    null_sd: float
    detail: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "statistic": self.statistic,
            "observed": _round(self.observed),
            "n_perm": self.n_perm,
            "seed": self.seed,
            "p_two_sided": _round(self.p_two_sided),
            "p_one_sided_greater": _round(self.p_one_sided_greater),
            "null_mean": _round(self.null_mean),
            "null_sd": _round(self.null_sd),
            "detail": self.detail,
        }


def _cellB_arrays(frame: AnalysisFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (is_capable, salience, safe) int arrays for cell-B reps."""

    cell_b = list(frame.cell("B"))
    is_capable = np.fromiter(
        (1 if row.capability_band == CAPABLE else 0 for row in cell_b),
        dtype=np.int64,
        count=len(cell_b),
    )
    salience = np.fromiter(
        (row.salience for row in cell_b), dtype=np.int64, count=len(cell_b)
    )
    safe = np.fromiter(
        (1 if row.safe else 0 for row in cell_b), dtype=np.int64, count=len(cell_b)
    )
    return is_capable, salience, safe


def _band_delta(is_capable: np.ndarray, safe: np.ndarray) -> float:
    """capable safe-rate minus weak safe-rate."""

    cap_n = int(is_capable.sum())
    weak_n = int(is_capable.size - cap_n)
    if cap_n == 0 or weak_n == 0:
        raise ValueError("band delta needs both capable and weak reps in cell B")
    cap_rate = float(safe[is_capable == 1].mean())
    weak_rate = float(safe[is_capable == 0].mean())
    return cap_rate - weak_rate


def permutation_cellB_band(
    frame: AnalysisFrame, *, n_perm: int = 10000, seed: int = 0
) -> PermutationResult:
    """H1 primary test: capable vs weak safe rate in cell B by label permutation."""

    is_capable, _salience, safe = _cellB_arrays(frame)
    if is_capable.size == 0:
        raise ValueError("no cell-B reps to test")
    observed = _band_delta(is_capable, safe)

    rng = np.random.default_rng(seed)
    labels = is_capable.copy()
    null = np.empty(n_perm, dtype=np.float64)
    cap_n = int(is_capable.sum())
    weak_n = int(is_capable.size - cap_n)
    for i in range(n_perm):
        rng.shuffle(labels)
        cap_rate = safe[labels == 1].mean()
        weak_rate = safe[labels == 0].mean()
        null[i] = cap_rate - weak_rate

    p_two = (1 + int(np.sum(np.abs(null) >= abs(observed) - 1e-12))) / (n_perm + 1)
    p_greater = (1 + int(np.sum(null >= observed - 1e-12))) / (n_perm + 1)
    return PermutationResult(
        statistic="cellB_safe_rate(capable) - cellB_safe_rate(weak)",
        observed=observed,
        n_perm=n_perm,
        seed=seed,
        p_two_sided=p_two,
        p_one_sided_greater=p_greater,
        null_mean=float(null.mean()),
        null_sd=float(null.std()),
        detail={"capable_n": cap_n, "weak_n": weak_n},
    )


def _gap_by_level(
    is_capable: np.ndarray, salience: np.ndarray, safe: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Per-salience-level band gap (capable_rate - weak_rate).

    Returns (levels, gaps) for levels where BOTH bands have >= 1 rep; a level
    missing a band has no defined gap and is skipped.
    """

    levels: list[int] = []
    gaps: list[float] = []
    for level in np.unique(salience):
        mask = salience == level
        cap_mask = mask & (is_capable == 1)
        weak_mask = mask & (is_capable == 0)
        if not cap_mask.any() or not weak_mask.any():
            continue
        levels.append(int(level))
        gaps.append(float(safe[cap_mask].mean() - safe[weak_mask].mean()))
    return np.asarray(levels, dtype=np.float64), np.asarray(gaps, dtype=np.float64)


def _gap_trend_slope(levels: np.ndarray, gaps: np.ndarray) -> float:
    """OLS slope of the band gap on salience level.

    Uses every level with both bands present, so it reduces to (gap_hi - gap_lo)
    scaled by the level span for two levels and generalises to more. Blind to a
    salience main effect because a main effect leaves the per-level gap flat.
    """

    if levels.size < 2:
        raise ValueError(
            "interaction test needs >= 2 salience levels with both bands present"
        )
    xc = levels - levels.mean()
    denom = float(np.sum(xc * xc))
    if denom == 0.0:
        raise ValueError("salience levels are degenerate (zero variance)")
    return float(np.sum(xc * (gaps - gaps.mean())) / denom)


def permutation_interaction(
    frame: AnalysisFrame, *, n_perm: int = 10000, seed: int = 0
) -> PermutationResult:
    """H2 test: capability x salience interaction on the cell-B safe rate.

    Statistic = OLS slope of the per-level capable-minus-weak gap on salience.
    Null distribution = permute salience labels WITHIN each band (preserves each
    band's marginal safe rate and the band main effect; nulls the salience main
    effect and the interaction). Because the statistic is a gap trend, a pure
    salience main effect contributes nothing, so the test isolates the
    interaction.
    """

    is_capable, salience, safe = _cellB_arrays(frame)
    if is_capable.size == 0:
        raise ValueError("no cell-B reps to test")
    levels_obs, gaps_obs = _gap_by_level(is_capable, salience, safe)
    observed = _gap_trend_slope(levels_obs, gaps_obs)

    rng = np.random.default_rng(seed)
    cap_idx = np.where(is_capable == 1)[0]
    weak_idx = np.where(is_capable == 0)[0]
    perm_salience = salience.copy()
    null = np.empty(n_perm, dtype=np.float64)
    valid = 0
    for i in range(n_perm):
        # Independently permute the salience column within each band.
        perm_salience[cap_idx] = rng.permutation(salience[cap_idx])
        perm_salience[weak_idx] = rng.permutation(salience[weak_idx])
        levels_p, gaps_p = _gap_by_level(is_capable, perm_salience, safe)
        try:
            null[i] = _gap_trend_slope(levels_p, gaps_p)
            valid += 1
        except ValueError:
            null[i] = np.nan

    finite = null[np.isfinite(null)]
    if finite.size == 0:
        raise ValueError("interaction permutation produced no valid statistics")
    p_two = (1 + int(np.sum(np.abs(finite) >= abs(observed) - 1e-12))) / (
        finite.size + 1
    )
    p_greater = (1 + int(np.sum(finite >= observed - 1e-12))) / (finite.size + 1)
    return PermutationResult(
        statistic="OLS slope of cellB band gap (capable-weak) on salience",
        observed=observed,
        n_perm=int(finite.size),
        seed=seed,
        p_two_sided=p_two,
        p_one_sided_greater=p_greater,
        null_mean=float(finite.mean()),
        null_sd=float(finite.std()),
        detail={
            "levels": [int(x) for x in levels_obs.tolist()],
            "gaps": [_round(x) for x in gaps_obs.tolist()],
            "valid_perms": int(finite.size),
            "requested_perms": n_perm,
        },
    )


def permutation_report(
    frame: AnalysisFrame, *, n_perm: int = 10000, seed: int = 0
) -> dict[str, Any]:
    """Both pre-registered permutation tests as a deterministic report."""

    report: dict[str, Any] = {
        "schema_version": "governed_agent_bench.analysis.permutation.v1",
        "n_perm": n_perm,
        "seed": seed,
        "H1_cellB_capability_gate": permutation_cellB_band(
            frame, n_perm=n_perm, seed=seed
        ).as_dict(),
    }
    # H2 needs >= 2 salience levels with both bands present; report why if not.
    is_capable, salience, safe = _cellB_arrays(frame)
    levels, _gaps = _gap_by_level(is_capable, salience, safe)
    if levels.size >= 2:
        report["H2_capability_x_salience"] = permutation_interaction(
            frame, n_perm=n_perm, seed=seed
        ).as_dict()
    else:
        report["H2_capability_x_salience"] = {
            "skipped": True,
            "reason": "fewer than 2 salience levels with both bands present",
            "levels_with_both_bands": [int(x) for x in levels.tolist()],
        }
    return report


__all__ = [
    "PermutationResult",
    "permutation_cellB_band",
    "permutation_interaction",
    "permutation_report",
]
