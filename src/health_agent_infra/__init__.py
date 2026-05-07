"""Health Agent Infra — deterministic tooling for an agent-operated runtime.

Python modules in this package are the runtime's *tools*: data acquisition,
normalization, projection, classification, policy, synthesis, validation, and
review persistence. Markdown skills in the sibling ``skills/`` directory own
rationale, uncertainty, and clarification over actions the runtime has already
bounded.

See ``docs/hai/tour.md`` for the architecture walkthrough.
"""

from importlib.metadata import PackageNotFoundError, version as _metadata_version

try:
    __version__ = _metadata_version("health_agent_infra")
except PackageNotFoundError:
    # Source checkout without ``pip install -e .`` — tests add src/ to
    # sys.path so imports work but the distribution is not registered.
    # Fall back to a label that makes the un-installed state obvious
    # rather than advertising a stale version string.
    __version__ = "0.0.0+unregistered"
