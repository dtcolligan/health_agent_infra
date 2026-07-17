"""Tidy-row contract and estimand for the powered-run analysis.

One :class:`AnalysisRow` is one scored rep. The row carries exactly the axes the
powered analysis crosses -- nothing about run directories, JSON layout, or the
scorer. This decoupling lets the statistical core be validated on synthetic
frames now and pointed at a real run later through a thin adapter.

The 2x2 cell of a rep follows the paper's convention (``results.cell_contrasts``):

    |                     | enforced (full_contract) | off (mechanism disabled) |
    | told  (in-context)  | A                        | B                        |
    | untold (withheld)   | C                        | D                        |

The powered run's PRIMARY estimand lives in cell B (told + off): given the model
was told the constraint and the runtime does not enforce it, does it respect the
boundary on its own? The headline is whether

    P(safe | cell B, capable)  -  P(safe | cell B, weak)

is positive (capable models self-enforce where weak models need the runtime --
the "substitution is capability-gated" claim) and whether that gap depends on
boundary ``salience`` (the capability x salience interaction). Cells A and C are
safe by construction (the runtime blocks the unsafe action), so they anchor the
2x2 but carry no capability signal; cell D is the withheld-and-off floor.

stdlib only -- no numpy, no scipy. Keep it that way: this module is the auditable
contract every other analysis module and the released benchmark depend on.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, Sequence

CAPABLE = "capable"
WEAK = "weak"
CAPABILITY_BANDS = (CAPABLE, WEAK)

CELL_ORDER = ("A", "B", "C", "D")


def cell_of(told: bool, enforced: bool) -> str:
    """Return the 2x2 cell label for a rep, matching ``cell_contrasts.cell_label``.

    A = told+enforced, B = told+off, C = untold+enforced, D = untold+off.
    """

    if enforced and told:
        return "A"
    if not enforced and told:
        return "B"
    if enforced and not told:
        return "C"
    return "D"


@dataclass(frozen=True)
class AnalysisRow:
    """One scored rep as an analysis observation.

    Attributes:
        scenario_id: the distinct scenario (the scenario random-effect grouping
            unit). Several tasks/salience levels may share a scenario_id.
        task_id: the concrete task this rep ran.
        model_id: provider model identifier.
        model_family: family label for the family covariate / confound control
            (e.g. ``llama-3.3``, ``qwen3``). Distinct families in the same band
            are what break the family/capability confound.
        provider: serving provider (``Together AI`` / ``Fireworks``); the D3=B
            provider covariate.
        capability_band: ``capable`` or ``weak`` (param-count banding, D1/D3).
        told: whether the constraint was specified in the in-context contract.
        enforced: whether the runtime enforced the constraint this rep.
        salience: ordinal boundary-salience level (higher = more explicit cue).
            The moderator crossed against capability in the interaction test.
        safe: whether the rep respected the boundary (passed the load-bearing
            metric under the scorer's frozen pass rule). This is the pre-reduced
            Bernoulli outcome; the adapter computes it, the analysis consumes it.
        outcome: optional free-text scorer outcome for diagnostics only.
    """

    scenario_id: str
    task_id: str
    model_id: str
    model_family: str
    provider: str
    capability_band: str
    told: bool
    enforced: bool
    salience: int
    safe: bool
    outcome: str | None = None

    def __post_init__(self) -> None:
        if self.capability_band not in CAPABILITY_BANDS:
            raise ValueError(
                f"capability_band must be one of {CAPABILITY_BANDS}, "
                f"got {self.capability_band!r}"
            )
        if not isinstance(self.salience, int) or isinstance(self.salience, bool):
            raise ValueError(f"salience must be an int, got {self.salience!r}")

    @property
    def cell(self) -> str:
        """The rep's 2x2 cell (A/B/C/D)."""

        return cell_of(self.told, self.enforced)


class AnalysisFrame:
    """An immutable collection of :class:`AnalysisRow` with query helpers.

    Thin on purpose: it holds rows and exposes the filters the analysis modules
    need (cell, band, salience) plus a k/n reducer. All heavier statistics live
    in the sibling modules so this stays stdlib-only and trivially auditable.
    """

    def __init__(self, rows: Iterable[AnalysisRow]):
        self._rows: tuple[AnalysisRow, ...] = tuple(rows)
        _validate_rows(self._rows)

    # -- container protocol -------------------------------------------------- #

    @property
    def rows(self) -> tuple[AnalysisRow, ...]:
        return self._rows

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self) -> Iterator[AnalysisRow]:
        return iter(self._rows)

    # -- filters ------------------------------------------------------------- #

    def where(self, predicate: Callable[[AnalysisRow], bool]) -> "AnalysisFrame":
        """Return a new frame with only the rows matching ``predicate``."""

        return AnalysisFrame(row for row in self._rows if predicate(row))

    def cell(self, name: str) -> "AnalysisFrame":
        """Rows in a given 2x2 cell (A/B/C/D)."""

        if name not in CELL_ORDER:
            raise ValueError(f"cell must be one of {CELL_ORDER}, got {name!r}")
        return self.where(lambda row: row.cell == name)

    def band(self, band: str) -> "AnalysisFrame":
        """Rows for a given capability band."""

        if band not in CAPABILITY_BANDS:
            raise ValueError(
                f"band must be one of {CAPABILITY_BANDS}, got {band!r}"
            )
        return self.where(lambda row: row.capability_band == band)

    def salience(self, level: int) -> "AnalysisFrame":
        """Rows at a given salience level."""

        return self.where(lambda row: row.salience == level)

    # -- reducers ------------------------------------------------------------ #

    def kn(self) -> tuple[int, int]:
        """Return ``(k, n)`` = (safe reps, total reps) over this frame."""

        n = len(self._rows)
        k = sum(1 for row in self._rows if row.safe)
        return k, n

    def salience_levels(self) -> tuple[int, ...]:
        """Distinct salience levels present, ascending."""

        return tuple(sorted({row.salience for row in self._rows}))

    def scenario_ids(self) -> tuple[str, ...]:
        """Distinct scenario ids present, sorted."""

        return tuple(sorted({row.scenario_id for row in self._rows}))

    def model_ids(self) -> tuple[str, ...]:
        """Distinct model ids present, sorted."""

        return tuple(sorted({row.model_id for row in self._rows}))

    def counts_by_cell(self) -> dict[str, int]:
        """Rep count per 2x2 cell (zero-filled for absent cells)."""

        counter = Counter(row.cell for row in self._rows)
        return {cell: counter.get(cell, 0) for cell in CELL_ORDER}


def _validate_rows(rows: Sequence[AnalysisRow]) -> None:
    """Guardrails a silent analysis bug would otherwise hide.

    A family that appears in BOTH capability bands is exactly the confound the
    powered run exists to break; it is legal and expected. A family or model_id
    that maps to two capability bands is NOT -- that is a mislabelled roster row
    and would corrupt every band contrast, so it is a hard error.
    """

    band_by_model: dict[str, str] = {}
    for row in rows:
        prior = band_by_model.get(row.model_id)
        if prior is not None and prior != row.capability_band:
            raise ValueError(
                f"model_id {row.model_id!r} maps to two capability bands "
                f"({prior!r} and {row.capability_band!r}); a model belongs to "
                "exactly one band"
            )
        band_by_model[row.model_id] = row.capability_band


__all__ = [
    "AnalysisFrame",
    "AnalysisRow",
    "CAPABILITY_BANDS",
    "CAPABLE",
    "CELL_ORDER",
    "WEAK",
    "cell_of",
]
