"""W-E — merge-human-inputs skill consumes W-A presence tokens.

Per `hai/reporting/plans/v0_1_15/PLAN.md` §2.F.

Three required acceptance items:

  1. Skill reads from `hai intake gaps` and branches on
     `present.{nutrition, gym, readiness, sleep}.logged` to choose
     recap-first vs forward-march framing.
  2. Skill does NOT branch on `present.weigh_in.logged` because
     `hai intake weight` (W-B) is deferred to v0.1.17 — branching
     before the surface ships would create a dead path.
  3. (Optional `morning-ritual` skill, if shipped, asserts the
     four-step orchestration order — verbalize-only weigh-in.)
     **v0.1.15 ships the merge-human-inputs update only**; the
     standalone morning-ritual skill is deferred per the
     "optional (medium)" framing in PLAN §2.F. The OQ-1 + Codex
     round-2 ratification confirmed `verbalize-without-state-write`
     is sufficient for the gate session.
"""

from __future__ import annotations

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parents[1].parent
    / "src" / "health_agent_infra" / "skills" / "merge-human-inputs"
    / "SKILL.md"
)


def test_skill_md_exists():
    assert SKILL_PATH.exists(), f"merge-human-inputs SKILL.md missing at {SKILL_PATH}"


def test_skill_consumes_w_a_present_block_for_4_domains():
    """PLAN §2.F acceptance 1: skill explicitly reads
    `present.{nutrition, gym, readiness, sleep}.logged` from the W-A
    extension to `hai intake gaps` and branches its framing on those
    signals."""

    body = SKILL_PATH.read_text(encoding="utf-8")

    # The skill must reference the W-A `present` block by name.
    assert "present" in body, (
        "merge-human-inputs SKILL.md must reference the W-A 'present' "
        "block from `hai intake gaps`"
    )
    # Each of the 4 in-scope domains must be named in the W-A
    # consumption section.
    for domain in ("nutrition", "gym", "readiness", "sleep"):
        # Either `present.<domain>.logged` or `present.<domain>` is OK
        # as long as the skill clearly references the per-domain
        # presence signal.
        pattern = rf"present\.{domain}(\.logged)?"
        assert re.search(pattern, body), (
            f"SKILL.md must reference `present.{domain}.logged` (W-E acceptance 1; "
            f"the skill branches its framing on this signal)"
        )


def test_skill_does_not_branch_on_weigh_in_logged():
    """PLAN §2.F acceptance 2: skill explicitly does NOT branch on
    `present.weigh_in.logged`. W-B (intake weight) is deferred to
    v0.1.17; branching on a surface that doesn't ship would create
    a dead path. This is a defensive test that surfaces if a future
    maintainer adds the check before W-B ships."""

    body = SKILL_PATH.read_text(encoding="utf-8")

    # Allowed: a comment / supersede note that explicitly says NOT
    # to branch on weigh_in. Forbidden: an actual conditional that
    # consumes the field.
    forbidden_patterns = [
        r"if\s+present\.weigh_in\.logged",
        r"when\s+present\.weigh_in\.logged",
        r"present\.weigh_in\.logged\s*==\s*true",
        r"present\.weigh_in\.logged\s*is\s+true",
    ]
    for pat in forbidden_patterns:
        assert not re.search(pat, body, re.IGNORECASE), (
            f"SKILL.md must NOT branch on present.weigh_in.logged in "
            f"v0.1.15 (W-B deferred to v0.1.17). Found pattern: {pat!r}"
        )

    # Positive: the skill must explicitly note the exclusion so a
    # future contributor sees the constraint inline.
    assert "weigh_in" in body, (
        "SKILL.md must mention weigh_in by name (with the explicit "
        "exclusion-from-branching note) so future contributors see why"
    )


def test_skill_uses_recap_vs_forward_framing_vocabulary():
    """PLAN §2.F: the skill chooses recap-first framing when presence
    indicates the day already has logged events, and forward-march
    framing when it doesn't. Test asserts the framing vocabulary is
    present."""

    body = SKILL_PATH.read_text(encoding="utf-8")

    # The skill should use either "recap" or equivalent (e.g.
    # "review", "what you've done") and either "forward" or
    # equivalent (e.g. "morning check-in", "plan-for-today").
    assert "recap" in body.lower(), (
        "SKILL.md should include 'recap' vocabulary for the "
        "presence-true framing branch"
    )
    assert (
        "forward-march" in body.lower()
        or "forward march" in body.lower()
    ), (
        "SKILL.md should include 'forward-march' vocabulary for the "
        "presence-false framing branch"
    )
