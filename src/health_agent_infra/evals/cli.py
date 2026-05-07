"""`hai eval run` CLI wrappers.

Registered on the top-level ``hai`` dispatcher in
:mod:`health_agent_infra.cli`. This module has no side effects at
import time.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from .runner import (
    EvalRunError,
    SUPPORTED_DOMAINS,
    load_scenarios,
    run_scenarios,
)


def cmd_eval_run(args: argparse.Namespace) -> int:
    from health_agent_infra.core import exit_codes

    # v0.1.14 W-AN: --scenario-set <set> shorthand. Translates to the
    # underlying (kind, domain) pair, except for 'judge_adversarial'
    # which is fixture-only (W-AI corpus; no scoring path until v0.2.2
    # W58J wires the judge harness) and 'all' which fan-outs.
    scenario_set = getattr(args, "scenario_set", None)
    if scenario_set:
        if scenario_set == "judge_adversarial":
            return _emit_judge_adversarial_summary(args)
        if scenario_set == "factuality":
            return _run_factuality_corpus_scoring(args)
        if scenario_set == "all":
            return _run_all_scenario_sets(args)
        if scenario_set == "synthesis":
            kind = "synthesis"
            domain: Optional[str] = None
        else:
            kind = "domain"
            domain = scenario_set
    elif args.synthesis:
        kind = "synthesis"
        domain = None
    else:
        kind = "domain"
        domain = args.domain

    try:
        scenarios = load_scenarios(kind, domain=domain)
    except EvalRunError as exc:
        print(f"eval error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    if not scenarios:
        print(
            f"no scenarios found for kind={kind!r} domain={domain!r}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    try:
        scores = run_scenarios(scenarios)
    except EvalRunError as exc:
        print(f"eval error: {exc}", file=sys.stderr)
        return exit_codes.INTERNAL

    total = len(scores)
    passed = sum(1 for s in scores if s.passed)
    failed = total - passed

    if args.json:
        payload = {
            "kind": kind,
            "domain": domain,
            "total": total,
            "passed": passed,
            "failed": failed,
            "scores": [s.to_dict() for s in scores],
        }
        print(json.dumps(payload, indent=2))
    else:
        header = f"{kind}" + (f" / {domain}" if domain else "")
        print(f"eval {header}: {passed}/{total} passed ({failed} failed)")
        for s in scores:
            mark = "PASS" if s.passed else "FAIL"
            print(f"  [{mark}] {s.scenario_id}")
            if not s.passed:
                for axis, verdict in s.axes.items():
                    if verdict == "fail":
                        diff = s.diffs.get(axis, {})
                        print(f"      - {axis}: FAIL {diff}")

    # Scenario pass/fail outcome: OK when everything passed, USER_INPUT
    # when at least one failed — failed scenarios indicate a rubric /
    # runtime delta the caller can investigate, not a runtime crash.
    return exit_codes.OK if failed == 0 else exit_codes.USER_INPUT


def _run_factuality_corpus_scoring(args: argparse.Namespace) -> int:
    """v0.2.0 W58D: run the deterministic factuality corpus through
    the gate, compute pass/block percentages, and compare to the
    thresholds in ``policy.factuality_gate``.

    Output (JSON or human):
      - total fixtures, known-bad / known-good split
      - block_known_bad_pct (actual %) vs threshold
      - pass_known_good_pct (actual %) vs threshold
      - per-category counts

    Exit codes:
      - OK: both thresholds met
      - USER_INPUT: at least one threshold missed (scoring delta the
        caller can investigate, not a runtime crash — same convention
        as the domain runner)
      - INTERNAL: corpus or gate import failed
    """

    import sqlite3
    from importlib.resources import files

    from health_agent_infra.core import exit_codes
    from health_agent_infra.core.config import load_thresholds
    from health_agent_infra.core.eval import (
        ClaimGateInput,
        gate_claim,
    )

    fac_root = files("health_agent_infra").joinpath(
        "evals", "scenarios", "factuality"
    )
    index_path = fac_root.joinpath("index.json")
    if not index_path.is_file():
        print(
            "factuality index missing; v0.2.0 W58D corpus is incomplete",
            file=sys.stderr,
        )
        return exit_codes.INTERNAL

    index = json.loads(index_path.read_text(encoding="utf-8"))
    fixture_ids = [f["fixture_id"] for f in index["fixtures"]]

    # Seed an in-memory baseline DB. Importing here (not at module
    # top) keeps the corpus seed module out of the import surface
    # for non-W58D callers.
    from health_agent_infra.evals.scenarios.factuality._seed import (
        seed_factuality_baseline,
    )

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    seed_factuality_baseline(conn)

    known_bad_total = 0
    known_bad_blocked = 0
    known_good_total = 0
    known_good_passed = 0  # outcome != block
    per_category: dict[str, dict[str, int]] = {}
    failures: list[dict] = []

    for fixture_id in fixture_ids:
        fixture_path = fac_root.joinpath(f"{fixture_id}.json")
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        category = fixture["category"]
        expected = fixture["expected_outcome"]
        cat_bucket = per_category.setdefault(
            category, {"total": 0, "matched": 0},
        )
        cat_bucket["total"] += 1

        inp = fixture["input"]
        claim = ClaimGateInput(
            atom_text=inp["atom_text"],
            atom_type=inp["atom_type"],
            locator_set=inp.get("locator_set", []),
            audit_refs=inp.get("audit_refs", {}),
            user_id=inp.get("user_id"),
        )
        result = gate_claim(conn, claim)
        actual = result.outcome.value

        if expected == "block":
            known_bad_total += 1
            if actual == "block":
                known_bad_blocked += 1
                cat_bucket["matched"] += 1
            else:
                failures.append({
                    "fixture_id": fixture_id,
                    "expected": expected,
                    "actual": actual,
                    "block_reason": (
                        result.block_reason.value if result.block_reason
                        else None
                    ),
                })
        else:
            known_good_total += 1
            if actual != "block":
                known_good_passed += 1
                cat_bucket["matched"] += 1
            else:
                failures.append({
                    "fixture_id": fixture_id,
                    "expected": expected,
                    "actual": actual,
                    "block_reason": (
                        result.block_reason.value if result.block_reason
                        else None
                    ),
                })

    conn.close()

    # Compute percentages from manifest cardinality (no hard-coded
    # counts per F-PLAN-06).
    block_pct = (
        100.0 * known_bad_blocked / known_bad_total
        if known_bad_total else 0.0
    )
    pass_pct = (
        100.0 * known_good_passed / known_good_total
        if known_good_total else 0.0
    )

    thresholds = load_thresholds()
    gate_thresholds = thresholds["policy"]["factuality_gate"]
    block_min = float(gate_thresholds["block_known_bad_min_pct"])
    pass_min = float(gate_thresholds["pass_known_good_min_pct"])

    block_meets = block_pct >= block_min
    pass_meets = pass_pct >= pass_min
    overall_pass = block_meets and pass_meets

    payload = {
        "scenario_set": "factuality",
        "total_fixtures": len(fixture_ids),
        "known_bad": {
            "total": known_bad_total,
            "blocked": known_bad_blocked,
            "block_pct": round(block_pct, 4),
            "threshold_min_pct": block_min,
            "meets_threshold": block_meets,
        },
        "known_good": {
            "total": known_good_total,
            "passed": known_good_passed,
            "pass_pct": round(pass_pct, 4),
            "threshold_min_pct": pass_min,
            "meets_threshold": pass_meets,
        },
        "per_category": per_category,
        "failures": failures[:10],  # cap output size
        "failure_count": len(failures),
        "overall_pass": overall_pass,
    }

    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"factuality corpus: {len(fixture_ids)} fixtures")
        print(
            f"  known-bad: {known_bad_blocked}/{known_bad_total} "
            f"blocked ({block_pct:.2f}% — threshold ≥{block_min}%) "
            f"{'PASS' if block_meets else 'FAIL'}"
        )
        print(
            f"  known-good: {known_good_passed}/{known_good_total} "
            f"passed ({pass_pct:.2f}% — threshold ≥{pass_min}%) "
            f"{'PASS' if pass_meets else 'FAIL'}"
        )
        for cat, counts in sorted(per_category.items()):
            print(
                f"  {cat}: {counts['matched']}/{counts['total']}"
            )
        if failures:
            print(f"  failures ({len(failures)}):")
            for f in failures[:10]:
                print(
                    f"    - {f['fixture_id']}: expected "
                    f"{f['expected']}, got {f['actual']} "
                    f"({f['block_reason']})"
                )

    return exit_codes.OK if overall_pass else exit_codes.USER_INPUT


def _emit_judge_adversarial_summary(args: argparse.Namespace) -> int:
    """v0.1.14 W-AN + W-AI: emit shape summary of the judge-adversarial
    fixture corpus. No scoring; v0.2.2 W58J wires real judge calls."""

    from importlib.resources import files
    from health_agent_infra.core import exit_codes

    ja_root = files("health_agent_infra").joinpath(
        "evals", "scenarios", "judge_adversarial"
    )
    index_path = ja_root.joinpath("index.json")
    if not index_path.is_file():
        print(
            "judge_adversarial index missing; v0.1.14 W-AI fixture "
            "corpus is incomplete",
            file=sys.stderr,
        )
        return exit_codes.INTERNAL
    index = json.loads(index_path.read_text(encoding="utf-8"))
    summary = {
        "scenario_set": "judge_adversarial",
        "shape_only": True,
        "schema_version": index["schema_version"],
        "categories": {
            cat: len(ids) for cat, ids in index["categories"].items()
        },
        "total_fixtures": index["total_fixtures"],
        "scoring_state": (
            "no_scoring_until_v0_2_2_w58j_wires_judge_harness"
        ),
    }
    if getattr(args, "json", False):
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"judge-adversarial corpus ({index['total_fixtures']} fixtures):")
        for cat, count in summary["categories"].items():
            print(f"  {cat}: {count}")
        print("(no scoring; v0.2.2 W58J wires the judge harness)")
    return exit_codes.OK


def _run_all_scenario_sets(args: argparse.Namespace) -> int:
    """v0.1.14 W-AN: 'all' fan-out — runs every domain + synthesis
    + factuality sequentially. Returns first non-zero rc; OK on
    full pass.

    v0.2.0 W58D step 8 (per F-PLAN-R2-05 + PLAN §2.F acceptance #6):
    extends the fan-out to include the factuality corpus scoring.
    Both deterministic domain/synthesis sets and the factuality
    corpus are scored at 100% in 'all'. ``judge_adversarial`` stays
    shape-only summary (fixture corpus only — no scoring) until
    v0.2.2 W58J wires the judge harness; it is intentionally NOT
    in the 'all' fan-out.
    """

    from health_agent_infra.core import exit_codes

    rc_overall = exit_codes.OK
    # Deterministic domain + synthesis sets first.
    for set_name in sorted(SUPPORTED_DOMAINS) + ["synthesis"]:
        sub_args = argparse.Namespace(
            domain=set_name if set_name != "synthesis" else None,
            synthesis=(set_name == "synthesis"),
            scenario_set=None,
            json=getattr(args, "json", False),
        )
        rc = cmd_eval_run(sub_args)
        if rc != exit_codes.OK and rc_overall == exit_codes.OK:
            rc_overall = rc
    # Factuality corpus (W58D step 8 add).
    rc_fac = _run_factuality_corpus_scoring(args)
    if rc_fac != exit_codes.OK and rc_overall == exit_codes.OK:
        rc_overall = rc_fac
    return rc_overall


def cmd_eval_review(args: argparse.Namespace) -> int:
    """W-AI-2 (v0.1.17 §2.D) — `hai eval review` triage state operations.

    Subcommands: list / show / tag / dismiss / export. Persistence at
    ``~/.local/share/health_agent_infra/eval_review.json`` per OQ-2.
    """

    from health_agent_infra.core import exit_codes
    from health_agent_infra.evals import review

    op = args.review_command
    if op == "list":
        rows = review.list_corpus(
            corpus=args.corpus,
            tag_filter=args.tag,
            include_dismissed=args.include_dismissed,
        )
        print(json.dumps({
            "corpus": args.corpus,
            "count": len(rows),
            "rows": rows,
        }, indent=2, sort_keys=True))
        return exit_codes.OK

    if op == "show":
        bundle = review.show_scenario(args.scenario_id)
        if bundle is None:
            print(
                f"hai eval review show: scenario_id={args.scenario_id!r} "
                f"not found in fixture tree",
                file=sys.stderr,
            )
            return exit_codes.NOT_FOUND
        print(json.dumps(bundle, indent=2, sort_keys=True))
        return exit_codes.OK

    if op == "tag":
        if review.show_scenario(args.scenario_id) is None:
            print(
                f"hai eval review tag: unknown scenario_id "
                f"{args.scenario_id!r}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        entry = review.tag_scenario(
            args.scenario_id, tag=args.tag, note=args.note,
        )
        print(json.dumps(entry.to_dict(), indent=2, sort_keys=True))
        return exit_codes.OK

    if op == "dismiss":
        if review.show_scenario(args.scenario_id) is None:
            print(
                f"hai eval review dismiss: unknown scenario_id "
                f"{args.scenario_id!r}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        entry = review.dismiss_scenario(
            args.scenario_id, reason=args.reason,
        )
        print(json.dumps(entry.to_dict(), indent=2, sort_keys=True))
        return exit_codes.OK

    if op == "export":
        from pathlib import Path
        out = Path(args.output).expanduser()
        try:
            review.export_state(output=out, fmt=args.format)
        except ValueError as exc:
            print(f"hai eval review export: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT
        print(json.dumps({"exported_to": str(out), "format": args.format}))
        return exit_codes.OK

    # Should be unreachable — argparse `required=True`.
    print(
        f"hai eval review: unknown subcommand {op!r}",
        file=sys.stderr,
    )
    return exit_codes.USER_INPUT


def register_eval_subparser(sub: argparse._SubParsersAction) -> None:
    """Register the ``hai eval`` subparser tree on an existing dispatcher."""

    p_eval = sub.add_parser(
        "eval",
        help="Run evaluation scenarios against the deterministic runtime",
    )
    eval_sub = p_eval.add_subparsers(dest="eval_command", required=True)

    p_run = eval_sub.add_parser(
        "run",
        help="Execute scenarios for a domain or the synthesis layer",
    )
    group = p_run.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--domain",
        choices=sorted(SUPPORTED_DOMAINS),
        help="Run domain-level (classify + policy) scenarios for this domain",
    )
    group.add_argument(
        "--synthesis",
        action="store_true",
        help="Run synthesis-level (X-rule + run_synthesis) scenarios",
    )
    group.add_argument(
        "--scenario-set",
        choices=(
            sorted(SUPPORTED_DOMAINS)
            + ["synthesis", "judge_adversarial", "factuality", "all"]
        ),
        help=(
            "Run a named scenario set (v0.1.14 W-AN; v0.2.0 W58D adds "
            "'factuality'). 'all' runs every domain + synthesis + "
            "factuality (judge_adversarial is fixture-only and "
            "skipped from 'all' until v0.2.2 W58J wires the judge "
            "harness). 'judge_adversarial' enumerates the v0.1.14 W-AI "
            "fixture corpus shape-only — no scoring. 'factuality' "
            "scores the v0.2.0 W58D deterministic corpus against the "
            "policy.factuality_gate thresholds."
        ),
    )
    p_run.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable text",
    )
    p_run.set_defaults(func=cmd_eval_run)
    # Contract annotation — kept local to the eval module so the
    # packaged wheel's eval surface stays self-describing. The wider
    # capabilities module tolerates annotations anywhere in the tree.
    from health_agent_infra.core.capabilities import annotate_contract
    annotate_contract(
        p_run,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-in",
        exit_codes=("OK", "USER_INPUT", "INTERNAL"),
        agent_safe=True,
        description=(
            "Execute frozen deterministic eval scenarios for a domain "
            "(--domain) or the synthesis layer (--synthesis). Read-only "
            "— scores scenarios, never writes state. USER_INPUT when a "
            "scenario fails its rubric; INTERNAL if the runner itself "
            "crashes."
        ),
    )

    # W-AI-2 (v0.1.17 §2.D) — `hai eval review` triage state CLI.
    p_review = eval_sub.add_parser(
        "review",
        help=(
            "Triage state for the eval corpus (tag / dismiss / export). "
            "Persists to ~/.local/share/health_agent_infra/eval_review.json."
        ),
    )
    review_sub = p_review.add_subparsers(dest="review_command", required=True)

    p_rev_list = review_sub.add_parser(
        "list",
        help="List the live corpus with any per-scenario triage overlay.",
    )
    p_rev_list.add_argument(
        "--corpus", default="all",
        choices=("all", "scenarios", "judge_adversarial"),
        help=(
            "Which corpus to list. 'scenarios' = per-domain + synthesis "
            "fixture tree; 'judge_adversarial' = the W-AI judge corpus; "
            "'all' = both. Default: all."
        ),
    )
    p_rev_list.add_argument(
        "--tag", default=None,
        help="Filter to entries already carrying this triage tag.",
    )
    p_rev_list.add_argument(
        "--include-dismissed",
        action="store_true", dest="include_dismissed",
        help="Include rows that were dismissed (default: hide them).",
    )
    p_rev_list.set_defaults(func=cmd_eval_review)
    annotate_contract(
        p_rev_list,
        mutation="read-only", idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "List eval corpus with per-scenario triage overlay. Read-only."
        ),
    )

    p_rev_show = review_sub.add_parser(
        "show", help="Show one scenario's fixture body + triage state.",
    )
    p_rev_show.add_argument(
        "--scenario-id", required=True,
        help="The scenario_id from the fixture tree.",
    )
    p_rev_show.set_defaults(func=cmd_eval_review)
    annotate_contract(
        p_rev_show,
        mutation="read-only", idempotent="yes",
        json_output="default",
        exit_codes=("OK", "NOT_FOUND"),
        agent_safe=True,
        description="Show one scenario's full fixture + triage state.",
    )

    p_rev_tag = review_sub.add_parser(
        "tag",
        help=(
            "Set a triage tag on a scenario (persists to eval_review.json). "
            "Replaces any prior triage entry for that scenario."
        ),
    )
    p_rev_tag.add_argument("--scenario-id", required=True)
    p_rev_tag.add_argument(
        "--tag", required=True,
        help="Free-text triage tag (e.g. 'review-after-runtime-fix').",
    )
    p_rev_tag.add_argument("--note", default=None, help="Optional free-text note.")
    p_rev_tag.set_defaults(func=cmd_eval_review)
    annotate_contract(
        p_rev_tag,
        mutation="writes-state", idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Tag a scenario with a triage label. Per-user state; not the "
            "fixture tree itself (which is packaged read-only substrate)."
        ),
    )

    p_rev_dismiss = review_sub.add_parser(
        "dismiss",
        help=(
            "Mark a scenario dismissed with a reason. The scenario stays "
            "in the corpus but is hidden from default `list` output."
        ),
    )
    p_rev_dismiss.add_argument("--scenario-id", required=True)
    p_rev_dismiss.add_argument(
        "--reason", required=True,
        help="Free-text dismissal reason (e.g. 'fixture supersedes earlier rev').",
    )
    p_rev_dismiss.set_defaults(func=cmd_eval_review)
    annotate_contract(
        p_rev_dismiss,
        mutation="writes-state", idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Mark a scenario as dismissed in the per-user triage state.",
    )

    p_rev_export = review_sub.add_parser(
        "export",
        help="Export the full triage state to JSON or CSV.",
    )
    p_rev_export.add_argument(
        "--output", required=True,
        help="Destination path for the export.",
    )
    p_rev_export.add_argument(
        "--format", default="json", choices=("json", "csv"),
        help="Export format (default: json).",
    )
    p_rev_export.set_defaults(func=cmd_eval_review)
    annotate_contract(
        p_rev_export,
        mutation="read-only", idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Export the per-scenario triage state to a JSON or CSV file."
        ),
    )
