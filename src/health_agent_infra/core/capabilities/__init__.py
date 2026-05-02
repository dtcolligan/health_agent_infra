"""Agent-operable CLI contract — manifest generation and doc rendering.

Phase 2 of the agent-operable runtime plan (see
``reporting/plans/historical/agent_operable_runtime_plan.md §2``).

The CLI is the stable contract surface an agent host relies on. This
module is **manifest-first**: each subparser in ``cli.py`` carries a
small annotation block declaring its mutation class, idempotency, JSON
output mode, exit-code set, and whether it is agent-safe or
operator-only. The walker in :mod:`.walker` traverses the argparse tree
and emits a deterministic JSON manifest; :mod:`.render` regenerates the
human doc from that manifest.

Consumers:

- ``hai capabilities --json`` — emits the manifest to stdout (see
  ``cmd_capabilities`` in ``cli.py``).
- ``reporting/docs/agent_cli_contract.md`` — the human-readable doc,
  regenerated from the manifest on commit.
- The authoritative intent-routing skill (Phase 5) — consumes the
  manifest programmatically instead of maintaining its own mapping
  table.

Drift-proof by construction: a new subcommand without annotations
fails the coverage test (``test_every_subcommand_is_annotated``), so
the doc and the manifest can never diverge from the code.
"""

from health_agent_infra.core.capabilities.walker import (
    CONTRACT_KEYS,
    IDEMPOTENCY,
    JSON_OUTPUT_MODES,
    MUTATION_CLASSES,
    RELIABILITY_VALUES,
    ContractAnnotationError,
    annotate_choice_metadata,
    annotate_contract,
    build_manifest,
    walk_parser,
)

__all__ = [
    "CONTRACT_KEYS",
    "ContractAnnotationError",
    "IDEMPOTENCY",
    "JSON_OUTPUT_MODES",
    "MUTATION_CLASSES",
    "RELIABILITY_VALUES",
    "annotate_choice_metadata",
    "annotate_contract",
    "build_manifest",
    "walk_parser",
]
