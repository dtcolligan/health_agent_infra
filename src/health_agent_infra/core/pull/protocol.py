"""Protocol for runtime pull adapters.

``FlagshipPullAdapter`` is the historical internal name retained for
compatibility. The Protocol captures the thin runtime pull contract: a named source and a
deterministic loader that returns evidence in the dict shape
``health_agent_infra.core.clean.recovery_prep.clean_inputs`` consumes (keys
``sleep``, ``resting_hr``, ``hrv``, ``training_load``).

Conformance is structural — no inheritance required. See
``health_agent_infra.core.pull.garmin.GarminRecoveryReadinessAdapter`` for the
reference conformer.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable


@runtime_checkable
class FlagshipPullAdapter(Protocol):
    """Minimum contract for a pull adapter feeding the runtime.

    Conformers must:

      - expose a stable ``source_name`` attribute (string), used for
        provenance, logs, and operator-facing identification.
      - provide a ``load(as_of)`` method that returns a dict compatible
        with ``clean_inputs()`` — specifically keys ``sleep``,
        ``resting_hr``, ``hrv``, and ``training_load``.

    The Protocol intentionally does not encode the full dict shape in the
    type system; runtime compatibility with ``clean_inputs`` is the
    binding contract. This keeps the Protocol a thin adapter-level
    interface rather than a second schema.
    """

    source_name: str

    def load(self, as_of: date) -> dict:
        ...
