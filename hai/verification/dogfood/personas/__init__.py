"""Persona modules for the dogfood harness.

Each ``p<N>_<slug>.py`` module exports a single ``SPEC: PersonaSpec``
constant describing the synthetic user shape for that persona.
The runner walks ``ALL_PERSONAS`` and drives each through the
pipeline.

See ``base.py`` for the ``PersonaSpec`` dataclass and the helpers
each persona uses to build its evidence stream and state seeds.

v0.1.11 W-O expanded the matrix from 8 → 12: P9 (older female
endurance), P10 (adolescent recreational, below-spec contract),
P11 (elevated-stress hybrid, fills the F-C-06 stress-band gap),
P12 (vacation-returner, fills the data-discontinuity gap).
"""

from __future__ import annotations

from .base import PersonaSpec
from .p1_dom_baseline import SPEC as P1
from .p2_female_marathoner import SPEC as P2
from .p3_older_recreational import SPEC as P3
from .p4_strength_only_cutter import SPEC as P4
from .p5_female_multisport import SPEC as P5
from .p6_sporadic_recomp import SPEC as P6
from .p7_high_volume_hybrid import SPEC as P7
from .p8_day1_female_lifter import SPEC as P8
from .p9_older_female_endurance import SPEC as P9
from .p10_adolescent_recreational import SPEC as P10
from .p11_elevated_stress_hybrid import SPEC as P11
from .p12_vacation_returner import SPEC as P12
from .p13_low_domain_knowledge import SPEC as P13


ALL_PERSONAS: list[PersonaSpec] = [
    P1, P2, P3, P4, P5, P6, P7, P8,
    P9, P10, P11, P12, P13,
]


__all__ = [
    "ALL_PERSONAS",
    "PersonaSpec",
    "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8",
    "P9", "P10", "P11", "P12", "P13",
]
