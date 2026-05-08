"""Packaged persona fixtures (one JSON file per persona slug).

The directory itself is the contract surface — adding ``p2.json`` etc.
in v0.1.13 W-FBC-2 / W-Vb persona-replay does not require any code
change to the loader. ``core.demo.fixtures.load_fixture(slug)`` reads
``<slug>.json`` here via ``importlib.resources`` so a clean wheel
install can find the fixture without referring to the repo layout.
"""

from __future__ import annotations
