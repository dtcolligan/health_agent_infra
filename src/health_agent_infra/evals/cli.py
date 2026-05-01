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
    sequentially. Returns first non-zero rc; OK on full pass."""

    from health_agent_infra.core import exit_codes

    rc_overall = exit_codes.OK
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
    return rc_overall


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
        choices=sorted(SUPPORTED_DOMAINS) + ["synthesis", "judge_adversarial", "all"],
        help=(
            "Run a named scenario set (v0.1.14 W-AN). 'all' runs every "
            "domain + synthesis (judge_adversarial is fixture-only and "
            "skipped from 'all' until v0.2.2 W58J wires the judge "
            "harness). 'judge_adversarial' enumerates the v0.1.14 W-AI "
            "fixture corpus shape-only — no scoring."
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
