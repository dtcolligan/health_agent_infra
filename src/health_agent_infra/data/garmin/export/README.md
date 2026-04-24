# Packaged Garmin daily-summary fixture

`daily_summary_export.csv` is **synthetic seed data**. It does not represent
any real user's wearable export and ships only so the offline `hai pull
--source csv` adapter has something to read on a fresh install.

## Provenance

- 64 days of daily-summary rows across **early 2026** (deliberately future-
  dated relative to the seed origin so no one mistakes them for real
  historical data).
- Numeric columns only: HRV, RHR, sleep stage seconds, training-readiness
  components, ACWR, etc. Match the shape of the live Garmin Connect daily
  CSV export so the same `garmin.GarminRecoveryReadinessAdapter` reads both.
- **No names, email addresses, device serials, GPS coordinates, or other
  identifiers.** A regression test in `safety/tests/test_packaged_fixture_privacy.py`
  scans the file on every commit to keep this property load-bearing.

## What this fixture is for

- Bringing up a working `hai pull` → `hai clean` → `hai state snapshot`
  → `hai propose` → `hai synthesize` → `hai today` loop on a brand-new
  install **without any wearable account**.
- Exercising every projector and classifier path against deterministic
  inputs in CI.
- Letting contributors iterate on classifier thresholds + R-rule tuning
  with a stable reference dataset.

## What this fixture is NOT

- **Not anyone's real Garmin data.** No personal export was ever shipped
  in this package. If you find a column that looks like it might encode
  identity (a username field, an account id, a serial number), flag it
  on the issue tracker — it would be a regression worth fixing fast.
- **Not a clinical reference.** Values are plausible but not tied to any
  specific physiology; classifier behaviour against the fixture is a
  proof-of-life exercise, not a validation of any health claim.

## How to replace

A contributor regenerating this fixture should:

1. Hand-author or programmatically synthesize values that match the
   schema in `RAW_DAILY_ROW_COLUMNS` (see `core/pull/garmin_live.py` /
   `core/pull/intervals_icu.py`).
2. Pin dates in a deliberately future window so it's obviously seed data.
3. Re-run `safety/tests/test_packaged_fixture_privacy.py` to confirm the
   PII scan still passes.
4. Re-run the full test suite — many classifier tests depend on this
   fixture's specific values.

## Why this file exists at all

Because a privacy-first project should be auditable about what user data
it ships. Documenting "this is synthetic" beats letting future readers
wonder whether the package privately leaks an early contributor's vitals.
