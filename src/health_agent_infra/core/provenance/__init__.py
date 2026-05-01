"""Source-row provenance — typed locators back to evidence rows.

v0.1.14 W-PROV-1. See `reporting/docs/source_row_provenance.md`
for the full design contract. v0.2.0 W52 / W58D consume this
substrate; v0.1.14 demos it on recovery R6 firings.
"""

from health_agent_infra.core.provenance.locator import (
    LocatorValidationError,
    SourceRowLocator,
    dedupe_locators,
    locator_to_dict,
    resolve_locator,
    validate_locator,
)


__all__ = [
    "LocatorValidationError",
    "SourceRowLocator",
    "dedupe_locators",
    "locator_to_dict",
    "resolve_locator",
    "validate_locator",
]
