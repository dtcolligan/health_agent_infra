# Offline Garmin export adapter

Internal only. This adapter reads a local Garmin GDPR export zip and writes only derived runtime datasets under `data/garmin/export/`, which is already git-ignored.

## Run

From the repo root:

```bash
python3 garmin/import_export.py \
  /Users/myapplemini01/.openclaw/media/inbound/fbe9407f-8390-4805-aa81-e7c79afce0a9_1---fa114bc3-dbe0-477b-a716-0e35523dd6f0.zip
```

Optional custom output location:

```bash
python3 garmin/import_export.py /path/to/export.zip --output-dir /tmp/garmin-export
```

## Outputs

The script writes these derived files:

- `data/garmin/export/daily_summary_export.csv`
- `data/garmin/export/activities_export.csv`
- `data/garmin/export/hydration_events_export.csv`
- `data/garmin/export/health_status_pivot_export.csv`
- `data/garmin/export/manifest.json`

## Current supported sources

- UDS daily summary export
- sleep daily export
- training readiness export
- acute training load export
- training history export
- health status metric bundle, pivoted by metric type
- summarized activities export
- hydration log export

## Current limitations

- This is an offline adapter only, not a replacement for the live Garmin Connect pull path.
- It normalizes a bounded subset and does not yet emit the exact `clean_garmin.py` daily JSON contract.
- Health status metrics are pivoted only for top-level `value`, `status`, and baseline ranges.
- Activity units are normalized from export-style storage, using ms to sec, cm to m, and decimeters/sec to m/s assumptions from the provided file.
- Some export files mix date strings and epoch timestamps, so unsupported new file variants may need matcher updates.
- Nested FIT backups and richer activity splits/laps remain out of scope for this first pass.
