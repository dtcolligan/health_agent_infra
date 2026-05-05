"""W-Vb-4 (v0.1.17 §2.F) — persona-replay residual P7..P12.

Per Phase 0 finding F-PHASE0-07 (`reporting/plans/v0_1_17/audit_findings.md`):
all 13 personas (P1..P12 + P13 matrix-only) close cleanly at HEAD with
0 findings + 0 crashes. The W-Vb-4 acceptance items 1-2 + 4 are pre-
satisfied by v0.1.13/v0.1.14/v0.1.15 substrate work.

This test pins the cumulative closure as a regression contract: if a
future change re-introduces a crash on any P1..P12 persona, this test
fails before that change ships.

Acceptance per PLAN §2.F:
  1. Each persona reaches `synthesized` end-state (or honest defer).
  2. No persona crashes (Python exception, SQL error, validation fail).
  3. Per-persona JSON output — surfaced in summary.json + result.json.
  4. Cumulative count: P1..P12 close (12 of 12). P13 matrix-only.
  5. Three-at-a-time partial-closure pattern available (not used at
     v0.1.17 ship — F-PHASE0-07 closes all 12 cleanly).
  6. Matrix runtime documented (~5 min at v0.1.14 baseline; verified
     unchanged post-W-AH-2 expansion would update if breach).

The test runs the matrix in a tmp dir so it's hermetic. It is not a
CI gate (per AGENTS.md D10 — full matrix runs are not part of CI),
but lives in the test surface so the contract is discoverable. To run
explicitly:
    uv run pytest verification/tests/test_w_vb_4_persona_matrix_baseline.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# Skip-by-default: this test takes ~5 minutes and intentionally lives
# outside CI per AGENTS.md D10. Run explicitly when verifying W-Vb-4
# closure or after substrate expansion (W-AH-2 / W-AM-2). Override via
# HAI_RUN_PERSONA_MATRIX=1 to include.
import os

_EXPLICIT = os.environ.get("HAI_RUN_PERSONA_MATRIX") == "1"

pytestmark = pytest.mark.skipif(
    not _EXPLICIT,
    reason=(
        "Persona matrix is opt-in (~5min runtime; per AGENTS.md D10 "
        "full matrix runs are not CI gates). Set "
        "HAI_RUN_PERSONA_MATRIX=1 to run."
    ),
)


def test_persona_matrix_p1_through_p12_close_with_no_findings_or_crashes(
    tmp_path,
):
    """W-Vb-4 acceptance items 1-4: 12-of-12 cumulative persona closure
    with 0 findings + 0 crashes. P13 matrix-only doesn't gate."""

    out_dir = tmp_path / "persona_run"
    proc = subprocess.run(
        [
            sys.executable, "-m", "verification.dogfood.runner",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        timeout=900,
    )
    # Runner exit code is informational; the contract under test is
    # the summary.json contents.
    assert proc.returncode == 0, (
        f"persona matrix runner exited {proc.returncode}: {proc.stderr[:500]}"
    )

    summary_path = out_dir / "summary.json"
    assert summary_path.exists(), f"summary.json missing at {summary_path}"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["n_personas"] >= 12, (
        f"expected ≥12 personas, got {summary['n_personas']}"
    )
    assert summary["total_crashes"] == 0, (
        f"persona matrix crashes ({summary['total_crashes']}): "
        f"{json.dumps(summary['findings_by_kind'], indent=2)[:500]}"
    )
    assert summary["total_findings"] == 0, (
        f"persona matrix findings ({summary['total_findings']}): "
        f"{json.dumps(summary['findings_by_kind'], indent=2)[:500]}"
    )

    # Each P1..P12 persona produced a result.json (W-Vb-4 §2.F item 3).
    for pid in (
        "p1_dom_baseline", "p2_female_marathoner", "p3_older_recreational",
        "p4_strength_only_cutter", "p5_female_multisport",
        "p6_sporadic_recomp", "p7_high_volume_hybrid",
        "p8_day1_female_lifter", "p9_older_female_endurance",
        "p10_adolescent_recreational", "p11_elevated_stress_hybrid",
        "p12_vacation_returner",
    ):
        result_path = out_dir / pid / "result.json"
        assert result_path.exists(), (
            f"persona {pid}: result.json missing at {result_path}"
        )
