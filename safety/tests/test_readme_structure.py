"""D3 test #10 — README structure contract.

The README is a live artifact — reviewers scan it to decide whether to
try the project. These assertions pin the structural changes ratified
in D3 (`reporting/plans/v0_1_4/D3_user_surface.md`):

- **Quickstart includes `hai today`** as a first-class step.
- **New "Reading your plan" section** describing `hai today`.
- **New "Recording your day" section** covering `hai review record`.
- **Architecture note discouraging raw SQL reads** in favour of the
  CLI surfaces that handle supersede chains + schema churn.

The check is structural — matches section headers and command
references, not prose style. Voice drift is caught by the voice
linter + the narration tests.
"""

from __future__ import annotations

from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_README = _REPO_ROOT / "README.md"


def _readme() -> str:
    assert _README.exists(), f"README.md not found at {_README}"
    return _README.read_text(encoding="utf-8")


def test_quickstart_includes_hai_today():
    """The first-install quickstart block must introduce `hai today`
    alongside `hai daily` so new users discover the read surface
    immediately, not after digging through docs.
    """

    body = _readme()
    install_start = body.find("## Install")
    next_section = body.find("\n## ", install_start + 1)
    assert install_start != -1
    assert next_section != -1
    # Walk forward through Install AND Reading your plan so the
    # quickstart's `hai today` anchor stays visible even as the
    # following section expands.
    install_section = body[install_start:next_section]
    assert "hai today" in install_section, (
        "`hai today` must appear in the Install / quickstart section "
        "alongside `hai daily`."
    )


def test_reading_your_plan_section_exists():
    body = _readme()
    assert "## Reading your plan" in body, (
        "README is missing the `## Reading your plan` section specified "
        "in reporting/plans/v0_1_4/D3_user_surface.md."
    )


def test_recording_your_day_section_exists():
    body = _readme()
    assert "## Recording your day" in body, (
        "README is missing the `## Recording your day` section specified "
        "in reporting/plans/v0_1_4/D3_user_surface.md."
    )


def test_reading_your_plan_references_hai_today_invocations():
    """The section should teach the core invocations so a reader can
    copy-paste. Not a snapshot — just presence checks for the flags
    D3 names as important."""

    body = _readme()
    start = body.find("## Reading your plan")
    next_section = body.find("\n## ", start + 1)
    section = body[start:next_section] if next_section != -1 else body[start:]

    assert "hai today" in section
    assert "--as-of" in section
    assert "--domain" in section
    assert "--format" in section
    # Operator surface must be cross-referenced so a reader who wants
    # the raw audit dump knows where to go.
    assert "hai explain --operator" in section


def test_recording_your_day_references_review_record_and_summary():
    body = _readme()
    start = body.find("## Recording your day")
    next_section = body.find("\n## ", start + 1)
    section = body[start:next_section] if next_section != -1 else body[start:]

    assert "hai review record" in section
    assert "hai review summary" in section
    # The re-link-on-supersede behavior is non-obvious — D3 requires
    # it be called out so users understand why their outcome lands on
    # the "wrong" rec id after a re-author.
    lowered = section.lower()
    assert "supersede" in lowered or "re-link" in lowered or "canonical leaf" in lowered


def test_architecture_bullet_points_users_at_hai_today_not_raw_sql():
    """The bullet that used to suggest `plain SQL` now nudges users
    toward the CLI surfaces that reconcile supersede chains. This is
    the "don't read SQLite directly" note D3 asks for.
    """

    body = _readme()
    # The bullet sits in the auditability paragraph above the Install
    # section. Not pinning exact wording, but the bullet must prefer
    # `hai today` to `plain SQL`.
    auditable_idx = body.find("Auditable by construction")
    assert auditable_idx != -1
    end_idx = body.find("## Install", auditable_idx)
    bullet = body[auditable_idx:end_idx]

    assert "hai today" in bullet, (
        "Auditable-by-construction bullet should prefer `hai today` over "
        "raw SQLite reads (D3)."
    )
    # Past wording literally said "or plain SQL." Guard against that
    # exact phrase sneaking back in (the bullet can still mention SQL
    # as a fallback, but not as an equal-footing option).
    assert "or plain SQL." not in bullet, (
        "README still offers plain SQL as a first-class inspection "
        "option — D3 wants users nudged toward `hai today` / "
        "`hai explain --operator` instead."
    )
