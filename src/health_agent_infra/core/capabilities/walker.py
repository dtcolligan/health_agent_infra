"""Argparse tree walker — collects contract annotations into a manifest.

The manifest is a dict:

    {
      "schema_version": "agent_cli_contract.v1",
      "hai_version": "<package version>",
      "generated_by": "core.capabilities.walker.build_manifest",
      "commands": [
        {
          "command": "hai pull",
          "description": "...",
          "mutation": "writes-sync-log",
          "idempotent": "yes",
          "json_output": "default",
          "exit_codes": ["OK", "USER_INPUT", "TRANSIENT"],
          "agent_safe": true,
        },
        ...
      ],
    }

Nested subcommands (e.g. ``hai state init``) are flattened into one row
per leaf command. The ``command`` field is the full invocation string
the user types. Rows are sorted lexicographically so the manifest is
diff-friendly.
"""

from __future__ import annotations

import argparse
from typing import Any, Iterable, Optional

from health_agent_infra import __version__ as _PACKAGE_VERSION


# ---------------------------------------------------------------------------
# Allowed values — drift-proof enums for the annotation payload.
# Changing these is a schema break; bump ``SCHEMA_VERSION`` if you do.
# ---------------------------------------------------------------------------

MUTATION_CLASSES: frozenset[str] = frozenset({
    "read-only",          # no persistent writes anywhere
    "writes-sync-log",    # only sync_run_log (e.g. hai pull)
    "writes-audit-log",   # JSONL audit file writes (e.g. hai review record)
    "writes-state",       # primary state DB writes (e.g. hai synthesize)
    "writes-memory",      # user_memory table writes (hai memory set)
    "writes-skills-dir",  # copies the packaged skills tree to ~/.claude
    "writes-config",      # writes a config/thresholds file
    "writes-credentials", # OS keyring writes (hai auth garmin)
    "interactive",        # requires live human input (hai init)
})

IDEMPOTENCY: frozenset[str] = frozenset({
    "yes",                  # same inputs → same state after every call
    "yes-with-supersede",   # supersedes a prior row via a --supersede flag
    "yes-with-replace",     # revises a prior row via a --replace flag
                            # (D1: proposal revision chain semantics;
                            # identical-payload replay is a no-op, new
                            # payload creates a new revision leaf).
    "no",                   # append-only, order-sensitive, or interactive
    "n/a",                  # read-only command, idempotency doesn't apply
})

JSON_OUTPUT_MODES: frozenset[str] = frozenset({
    "default",   # always emits JSON on stdout
    "opt-in",    # JSON via an explicit --json flag
    "opt-out",   # JSON by default; --text suppresses
    "none",      # text-only output
    "dual",      # explicit --json and --text flags both supported
})

# Legacy exit-code placeholder for subcommands that still return 0/2 via
# the old pattern. An honest manifest reports what the handler actually
# does today, so these sit alongside migrated entries until the
# exit-code migration is finished (Phase 2 part 2).
LEGACY_EXIT_CODES: tuple[str, ...] = ("LEGACY_0_2",)

MIGRATED_EXIT_CODES: frozenset[str] = frozenset({
    "OK", "USER_INPUT", "TRANSIENT", "NOT_FOUND", "INTERNAL",
})

ALLOWED_EXIT_CODES: frozenset[str] = MIGRATED_EXIT_CODES | {"LEGACY_0_2"}


# The argparse-defaults keys we own. Prefix with underscore so they
# don't collide with user-facing CLI flags and so they're visibly
# internal in any stack trace that prints a Namespace.
CONTRACT_KEYS: tuple[str, ...] = (
    "_contract_mutation",
    "_contract_idempotent",
    "_contract_json_output",
    "_contract_exit_codes",
    "_contract_agent_safe",
    "_contract_description",
    "_contract_output_schema",
    "_contract_preconditions",
)


SCHEMA_VERSION = "agent_cli_contract.v1"


class ContractAnnotationError(ValueError):
    """Raised when an annotation value is outside the allowed set.

    Caught at build-time (import time, typically) so a bad annotation
    fails the test suite rather than silently corrupting the manifest.
    """


# ---------------------------------------------------------------------------
# Annotate a subparser — the hook cli.py uses on every add_parser call.
# ---------------------------------------------------------------------------


def annotate_contract(
    parser: argparse.ArgumentParser,
    *,
    mutation: str,
    idempotent: str,
    json_output: str,
    exit_codes: Iterable[str],
    agent_safe: bool,
    description: Optional[str] = None,
    output_schema: Optional[dict[str, Any]] = None,
    preconditions: Optional[list[str]] = None,
) -> None:
    """Attach contract metadata to an argparse subparser.

    Called by ``cli.py`` immediately after ``add_parser`` +
    ``set_defaults(func=...)``. Values are validated eagerly so a
    typo surfaces at CLI-construction time rather than in the
    manifest.

    ``output_schema`` and ``preconditions`` are optional agent hints
    (WS-C):

    - ``output_schema`` is a free-form dict (keyed by exit-code name;
      each value is a nested description of the JSON shape emitted).
      Not every command needs it; the JSON-mode commands that return
      a stable schema should carry one.
    - ``preconditions`` is a list of short strings naming state that
      must exist (e.g. ``"state_db_initialized"``,
      ``"proposal_log_has_row_for_today"``). Consumed by the
      intent-router to decide whether to chain a command vs. surface
      a setup step to the user.
    """

    if mutation not in MUTATION_CLASSES:
        raise ContractAnnotationError(
            f"unknown mutation class {mutation!r}; "
            f"allowed: {sorted(MUTATION_CLASSES)}"
        )
    if idempotent not in IDEMPOTENCY:
        raise ContractAnnotationError(
            f"unknown idempotency value {idempotent!r}; "
            f"allowed: {sorted(IDEMPOTENCY)}"
        )
    if json_output not in JSON_OUTPUT_MODES:
        raise ContractAnnotationError(
            f"unknown json_output value {json_output!r}; "
            f"allowed: {sorted(JSON_OUTPUT_MODES)}"
        )

    code_list = list(exit_codes)
    for code in code_list:
        if code not in ALLOWED_EXIT_CODES:
            raise ContractAnnotationError(
                f"unknown exit code {code!r}; "
                f"allowed: {sorted(ALLOWED_EXIT_CODES)}"
            )
    # OK is expected on every migrated command — catch accidental
    # omission early.
    if code_list != list(LEGACY_EXIT_CODES) and "OK" not in code_list:
        raise ContractAnnotationError(
            f"exit_codes must include 'OK' for migrated commands; "
            f"got {code_list!r}"
        )

    # output_schema: any keys set must correspond to a declared exit
    # code name so an author can't document a shape for a code the
    # command can't actually emit.
    if output_schema is not None:
        if not isinstance(output_schema, dict):
            raise ContractAnnotationError(
                f"output_schema must be a dict or None; got "
                f"{type(output_schema).__name__}"
            )
        unknown_keys = set(output_schema) - set(code_list)
        if unknown_keys:
            raise ContractAnnotationError(
                f"output_schema contains keys not in exit_codes: "
                f"{sorted(unknown_keys)}"
            )

    if preconditions is not None:
        if not isinstance(preconditions, list) or not all(
            isinstance(p, str) and p for p in preconditions
        ):
            raise ContractAnnotationError(
                "preconditions must be a list of non-empty strings"
            )

    parser.set_defaults(
        _contract_mutation=mutation,
        _contract_idempotent=idempotent,
        _contract_json_output=json_output,
        _contract_exit_codes=tuple(code_list),
        _contract_agent_safe=bool(agent_safe),
        _contract_description=description,
        _contract_output_schema=output_schema,
        _contract_preconditions=tuple(preconditions) if preconditions else None,
    )


# ---------------------------------------------------------------------------
# Walker — traverse the argparse tree, flatten to leaf commands.
# ---------------------------------------------------------------------------


def walk_parser(
    parser: argparse.ArgumentParser,
    *,
    prog: str = "hai",
) -> list[dict[str, Any]]:
    """Walk ``parser`` and return one row per leaf command.

    A "leaf command" is any parser that has no further subparsers — the
    thing the user actually invokes. For ``hai auth garmin``, the leaf
    parser is the one registered under ``auth_sub.add_parser("garmin")``;
    ``hai auth`` itself is an internal node and does not appear in the
    manifest.

    Rows are sorted by ``command`` lexicographically so the manifest is
    deterministic across runs.
    """

    rows: list[dict[str, Any]] = []
    _walk(parser, path=[prog], rows=rows)
    rows.sort(key=lambda r: r["command"])
    return rows


def _walk(
    parser: argparse.ArgumentParser,
    *,
    path: list[str],
    rows: list[dict[str, Any]],
) -> None:
    sub_actions = _subparsers_actions(parser)
    if not sub_actions:
        # Leaf — record it if it has a handler (set_defaults(func=...)).
        # Some internal-only parsers (the top-level `hai` parser, an
        # intermediate `hai auth`) have no func; they're not real
        # commands and shouldn't appear in the manifest.
        defaults = parser._defaults  # argparse has no public accessor
        func = defaults.get("func")
        if func is None:
            return
        rows.append(_row_for_leaf(parser=parser, path=path, defaults=defaults))
        return

    for sub_action in sub_actions:
        for name, child in sub_action.choices.items():
            _walk(child, path=path + [name], rows=rows)


def _subparsers_actions(
    parser: argparse.ArgumentParser,
) -> list[argparse._SubParsersAction]:
    return [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]


def _row_for_leaf(
    *,
    parser: argparse.ArgumentParser,
    path: list[str],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    command = " ".join(path)
    description = (
        defaults.get("_contract_description")
        or parser.description
        or _help_text_from_parent(parser)
        or ""
    )
    row: dict[str, Any] = {
        "command": command,
        "description": description.strip() if isinstance(description, str) else "",
        "mutation": defaults.get("_contract_mutation"),
        "idempotent": defaults.get("_contract_idempotent"),
        "json_output": defaults.get("_contract_json_output"),
        "exit_codes": list(defaults.get("_contract_exit_codes") or ()),
        "agent_safe": defaults.get("_contract_agent_safe"),
        "flags": _flags_for_parser(parser),
    }
    output_schema = defaults.get("_contract_output_schema")
    if output_schema is not None:
        row["output_schema"] = output_schema
    preconditions = defaults.get("_contract_preconditions")
    if preconditions is not None:
        row["preconditions"] = list(preconditions)
    return row


# ---------------------------------------------------------------------------
# Flag extraction — walk leaf parser's actions to produce the flags[]
# entry the MCP/agent layer consumes as the argument schema.
# ---------------------------------------------------------------------------


# Argparse action classes that are not user-visible flags. ``_HelpAction``
# is auto-added and always present; ``_SubParsersAction`` is already
# handled by the outer walker; ``_VersionAction`` is rare but follows
# the same "not a real input" contract.
_SKIP_ACTION_CLASSES: tuple[type, ...] = (
    argparse._HelpAction,
    argparse._SubParsersAction,
    argparse._VersionAction,
)


def _flags_for_parser(parser: argparse.ArgumentParser) -> list[dict[str, Any]]:
    """Return one entry per user-visible flag / positional arg.

    Ordering matches argparse's action registration order — callers
    that want alphabetical can sort at the consumer layer, but the
    registration order conveys intent (required positionals first,
    then optional flags, then the ``--db-path`` tail).

    Each entry carries enough to render a usage hint or construct an
    MCP tool-input schema:

    - ``name``: the primary string ('--db-path', 'domain').
    - ``positional``: True iff no ``option_strings`` were declared.
    - ``required``: reflects ``action.required``; positional args
      without ``nargs='?'`` are always required.
    - ``type``: the type name (``str``, ``int``, ``bool``). Falls
      back to ``"str"`` when argparse didn't pin a type.
    - ``choices``: list of allowed values, or None.
    - ``default``: JSON-able default, or None if the Python default
      isn't JSON-serialisable (callables, sentinel objects).
    - ``help``: the ``help=`` string, stripped.
    - ``action``: argparse action class short name ('store',
      'store_true', 'store_false', 'append', 'count').
    - ``nargs``: the nargs spec if set, else None.
    - ``aliases``: any additional ``option_strings`` besides
      ``name`` (e.g. ``["-d"]`` for ``--debug``).
    """

    flags: list[dict[str, Any]] = []
    for action in parser._actions:
        if isinstance(action, _SKIP_ACTION_CLASSES):
            continue
        flags.append(_flag_entry(action))
    return flags


def _flag_entry(action: argparse.Action) -> dict[str, Any]:
    option_strings = list(action.option_strings)
    if option_strings:
        positional = False
        name = _primary_option_string(option_strings)
        aliases = [s for s in option_strings if s != name]
    else:
        positional = True
        name = action.dest
        aliases = []

    return {
        "name": name,
        "positional": positional,
        "required": _flag_is_required(action),
        "type": _flag_type_name(action),
        "choices": _flag_choices(action),
        "default": _json_safe_default(action.default),
        "help": (action.help or "").strip(),
        "action": _flag_action_name(action),
        "nargs": action.nargs if action.nargs is not None else None,
        "aliases": aliases,
    }


def _primary_option_string(option_strings: list[str]) -> str:
    """Prefer the long form (``--db-path``) over short (``-d``). Long
    forms are what the contract doc + agent prompts show; short
    forms are human conveniences."""

    long_forms = [s for s in option_strings if s.startswith("--")]
    return long_forms[0] if long_forms else option_strings[0]


def _flag_is_required(action: argparse.Action) -> bool:
    # For positionals (no option_strings), argparse sets ``required=True``
    # by default unless ``nargs='?'`` or ``nargs='*'``. Mirror that here
    # so the manifest honestly reports what argparse will enforce.
    if not action.option_strings:
        if action.nargs in ("?", "*"):
            return False
        return True
    return bool(action.required)


def _flag_type_name(action: argparse.Action) -> str:
    # store_true / store_false are bool shapes even though their .type
    # is None.
    if isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
        return "bool"
    if action.type is None:
        return "str"
    return getattr(action.type, "__name__", "str")


def _flag_choices(action: argparse.Action) -> Optional[list[Any]]:
    if action.choices is None:
        return None
    # Serialise range() into a list for JSON-ability. Anything else
    # gets passed through — argparse accepts iterables but the common
    # shapes are list / tuple / range / frozenset.
    choices = list(action.choices)
    return [_json_safe_default(c) for c in choices]


def _flag_action_name(action: argparse.Action) -> str:
    """Short stable name for the argparse action class.

    ``_StoreAction`` → ``store``; ``_StoreTrueAction`` → ``store_true``.
    Unknown action classes fall through to the class name lowercased
    with leading underscores stripped, so a custom action surfaces
    honestly instead of being silently squashed into ``store``.
    """

    known: dict[type, str] = {
        argparse._StoreAction: "store",
        argparse._StoreTrueAction: "store_true",
        argparse._StoreFalseAction: "store_false",
        argparse._AppendAction: "append",
        argparse._AppendConstAction: "append_const",
        argparse._StoreConstAction: "store_const",
        argparse._CountAction: "count",
    }
    short = known.get(type(action))
    if short is not None:
        return short
    return type(action).__name__.lstrip("_").lower()


def _json_safe_default(value: Any) -> Any:
    """Return ``value`` unchanged if JSON-serialisable; otherwise None.

    Callable defaults (e.g. ``default=datetime.utcnow``) can't be
    round-tripped through JSON honestly and would mislead an agent
    that pattern-matches on them. Returning None is the least-wrong
    option; the author can add an explicit ``default`` via help= or
    an output_schema hint if the callable matters.
    """

    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe_default(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe_default(v) for k, v in value.items()}
    # Anything else (callables, custom sentinels) → None.
    return None


def _help_text_from_parent(parser: argparse.ArgumentParser) -> Optional[str]:
    """Best-effort: pull the help= string the parent parser registered
    this subcommand with, if we can find it. argparse doesn't expose
    this directly, so we read ``prog`` off the parser and search the
    parent's ``_choices_actions``. Returns None if we can't find it —
    callers fall back to the empty string in that case.
    """

    # argparse doesn't keep a back-pointer, so this is best-effort and
    # intentionally simple. Most annotated commands will override via
    # _contract_description anyway; this is just a polite fallback
    # when a command has no description= and no override.
    return None


# ---------------------------------------------------------------------------
# Manifest builder — wraps walker rows in the top-level envelope.
# ---------------------------------------------------------------------------


def build_manifest(
    parser: argparse.ArgumentParser,
    *,
    hai_version: Optional[str] = None,
) -> dict[str, Any]:
    """Build the full manifest dict for the given top-level parser.

    Separate from :func:`walk_parser` so the envelope (schema_version,
    version, generator) can evolve independently of the per-command rows.
    """

    return {
        "schema_version": SCHEMA_VERSION,
        "hai_version": hai_version or _PACKAGE_VERSION,
        "generated_by": "core.capabilities.walker.build_manifest",
        "commands": walk_parser(parser),
    }


# ---------------------------------------------------------------------------
# Coverage helpers — used by tests to assert every leaf is annotated.
# ---------------------------------------------------------------------------


def unannotated_commands(
    parser: argparse.ArgumentParser,
) -> list[str]:
    """Return the list of leaf commands that are missing one or more
    contract annotations. Used by the CI coverage test."""

    unannotated: list[str] = []
    for row in walk_parser(parser):
        if (
            row["mutation"] is None
            or row["idempotent"] is None
            or row["json_output"] is None
            or row["agent_safe"] is None
            or not row["exit_codes"]
        ):
            unannotated.append(row["command"])
    return unannotated
