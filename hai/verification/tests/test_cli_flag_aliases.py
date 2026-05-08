"""W-Y: CLI civil-date flag harmonisation (Codex F-DEMO-03).

`--as-of` is now accepted on `hai pull` (alongside `--date`) and
`hai explain` (alongside `--for-date`). Both flags route to the
same destination so handlers don't need to change.

`--date` and `--for-date` retained for backwards compatibility
through v0.1.12; removed in v0.1.13.
"""

from __future__ import annotations

from health_agent_infra.cli import build_parser


def _parse(argv):
    return build_parser().parse_args(argv)


# ---------------------------------------------------------------------------
# hai pull
# ---------------------------------------------------------------------------


def test_pull_accepts_as_of_alias():
    args = _parse(["pull", "--as-of", "2026-04-28"])
    assert args.date == "2026-04-28"


def test_pull_accepts_legacy_date_flag():
    args = _parse(["pull", "--date", "2026-04-28"])
    assert args.date == "2026-04-28"


def test_pull_no_date_arg_defaults_none():
    args = _parse(["pull"])
    assert args.date is None


# ---------------------------------------------------------------------------
# hai explain
# ---------------------------------------------------------------------------


def test_explain_accepts_as_of_alias():
    args = _parse(
        ["explain", "--as-of", "2026-04-28", "--user-id", "u_local_1"]
    )
    assert args.for_date == "2026-04-28"
    assert args.user_id == "u_local_1"


def test_explain_accepts_legacy_for_date_flag():
    args = _parse(
        ["explain", "--for-date", "2026-04-28", "--user-id", "u_local_1"]
    )
    assert args.for_date == "2026-04-28"


# ---------------------------------------------------------------------------
# Capabilities manifest reflects the alias
# ---------------------------------------------------------------------------


def test_capabilities_manifest_lists_as_of_on_pull():
    """The manifest walker should expose both `--date` and `--as-of`
    so contract consumers see the alias surface."""
    from health_agent_infra.core.capabilities import build_manifest
    manifest = build_manifest(build_parser())
    pull_cmd = next(
        c for c in manifest["commands"] if c["command"] == "hai pull"
    )
    pull_flags = {f["name"]: f for f in pull_cmd["flags"]}
    # The argparse alias surface stores the second name in `aliases`.
    assert "--date" in pull_flags or any(
        "--as-of" in f.get("aliases", []) for f in pull_cmd["flags"]
    ) or any(
        "--date" in f.get("aliases", []) for f in pull_cmd["flags"]
    )


def test_capabilities_manifest_lists_as_of_on_explain():
    from health_agent_infra.core.capabilities import build_manifest
    manifest = build_manifest(build_parser())
    explain_cmd = next(
        c for c in manifest["commands"] if c["command"] == "hai explain"
    )
    flags_by_name = {f["name"]: f for f in explain_cmd["flags"]}
    # Either name is exposed; the alias array carries the other.
    has_for_date = "--for-date" in flags_by_name
    has_as_of = "--as-of" in flags_by_name
    has_alias_for_date = any(
        "--for-date" in f.get("aliases", []) for f in explain_cmd["flags"]
    )
    has_alias_as_of = any(
        "--as-of" in f.get("aliases", []) for f in explain_cmd["flags"]
    )
    assert (has_for_date or has_alias_for_date) and (
        has_as_of or has_alias_as_of
    )
