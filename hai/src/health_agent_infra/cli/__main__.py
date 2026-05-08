"""Entry point for ``python -m health_agent_infra.cli``.

The wheel exposes the ``hai`` console script via the
``health_agent_infra.cli:main`` entry point in ``pyproject.toml``;
this module provides the equivalent surface for ``python -m`` so test
suites that shell out via ``[sys.executable, "-m", "health_agent_infra.cli", ...]``
continue to work after W-29's package layout split.
"""

import sys

from health_agent_infra.cli import main


if __name__ == "__main__":
    sys.exit(main())
