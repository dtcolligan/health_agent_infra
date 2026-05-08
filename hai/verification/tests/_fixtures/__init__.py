"""Fixture factories for v0.1.8 test suites.

Per ``reporting/plans/v0_1_8/PLAN.md`` § 0 (fixture-factory precondition)
and ``MAINTAINER_ANALYSIS.md`` § 4.3 / § 6.5: W48–W51 + W38 + W39 + W40 +
W43 + W45 + W46 will add ~80–120 tests that all need to seed
``intent_item``, ``target``, ``data_quality_daily``, and the
``recommendation_log → review_event → review_outcome`` chain. Without a
shared seeding API the boilerplate would be reinvented per file.

Two flavours of helper live here:

* **Pure dict builders** (``make_intent_row``, ``make_target_row``,
  ``make_outcome_chain``, ``make_data_quality_row``). Each takes sensible
  defaults plus override kwargs and returns a dict whose shape is pinned
  to PLAN.md § 2. The intent / target / data_quality builders ship today
  ahead of migrations 019 / 020 / 021 so consuming workstreams can wire
  their tests against the future schema without touching the dict shape
  more than once.
* **SQLite seeders** (``seed_outcome_chain``). Only land alongside the
  table they target. ``seed_outcome_chain`` ships today because the
  ``recommendation_log``, ``review_event``, and ``review_outcome`` tables
  already exist (migrations 001 + 003 + 010 + 016). Intent / target /
  data_quality seeders land with their migrations.

The leading underscore on the package name keeps these helpers out of
pytest's discovery path; the ``test_fixture_factory.py`` module here is
the one file pytest collects.
"""

from __future__ import annotations

from .builders import (
    make_data_quality_row,
    make_intent_row,
    make_outcome_chain,
    make_target_row,
)
from .seeders import seed_outcome_chain

__all__ = [
    "make_data_quality_row",
    "make_intent_row",
    "make_outcome_chain",
    "make_target_row",
    "seed_outcome_chain",
]
