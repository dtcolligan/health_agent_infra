from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from health_model.agent_interface import load_persisted_bundle
from health_model.agent_readable_daily_context import build_agent_readable_daily_context
from health_model.shared_input_backbone import validate_shared_input_bundle


def build_daily_context_artifact(*, bundle_path: str, user_id: str, date: str, output_dir: str) -> dict[str, Any]:
    bundle = load_persisted_bundle(bundle_path=bundle_path)
    output_path = Path(output_dir)

    validation = validate_shared_input_bundle(bundle)
    if not validation.is_valid:
        raise BundleValidationFailed(validation)

    artifact = build_agent_readable_daily_context(bundle, user_id=user_id, date=date)

    output_path.mkdir(parents=True, exist_ok=True)
    dated_path = output_path / f"agent_readable_daily_context_{date}.json"
    latest_path = output_path / "agent_readable_daily_context_latest.json"

    serialized = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    _write_artifact_pair_atomically(
        serialized=serialized,
        dated_path=dated_path,
        latest_path=latest_path,
    )

    return {
        "artifact": artifact,
        "dated_path": str(dated_path),
        "latest_path": str(latest_path),
    }


def _write_artifact_pair_atomically(*, serialized: str, dated_path: Path, latest_path: Path) -> None:
    original_states = {
        dated_path: _capture_file_state(dated_path),
        latest_path: _capture_file_state(latest_path),
    }
    temp_paths = {
        dated_path: _write_temp_artifact_file(target_path=dated_path, serialized=serialized),
        latest_path: _write_temp_artifact_file(target_path=latest_path, serialized=serialized),
    }

    try:
        _replace_artifact_file(source_path=temp_paths[dated_path], target_path=dated_path)
        _replace_artifact_file(source_path=temp_paths[latest_path], target_path=latest_path)
    except Exception:
        for target_path, state in original_states.items():
            _restore_artifact_file_state(target_path=target_path, state=state)
        raise
    finally:
        for temp_path in temp_paths.values():
            if temp_path.exists():
                temp_path.unlink()


def _capture_file_state(path: Path) -> dict[str, str | bool | None]:
    if not path.exists():
        return {"exists": False, "content": None}
    return {"exists": True, "content": path.read_text()}


def _write_temp_artifact_file(*, target_path: Path, serialized: str) -> Path:
    temp_path = target_path.with_name(f".{target_path.name}.{os.getpid()}.tmp")
    temp_path.write_text(serialized)
    return temp_path


def _replace_artifact_file(*, source_path: Path, target_path: Path) -> None:
    source_path.replace(target_path)


def _restore_artifact_file_state(*, target_path: Path, state: dict[str, str | bool | None]) -> None:
    if state["exists"]:
        target_path.write_text(str(state["content"]))
        return
    if target_path.exists():
        target_path.unlink()


class BundleValidationFailed(ValueError):
    def __init__(self, validation: Any) -> None:
        self.validation = validation
        super().__init__(self._message())

    def _message(self) -> str:
        issues = [
            *(f"schema:{issue.code} at {issue.path}: {issue.message}" for issue in self.validation.schema_issues),
            *(f"semantic:{issue.code} at {issue.path}: {issue.message}" for issue in self.validation.semantic_issues),
        ]
        return "Shared input bundle failed validation\n" + "\n".join(issues)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-path", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        result = build_daily_context_artifact(
            bundle_path=args.bundle_path,
            user_id=args.user_id,
            date=args.date,
            output_dir=args.output_dir,
        )
    except BundleValidationFailed as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(result["dated_path"])
    print(result["latest_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
