from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_ROOT = REPO_ROOT / 'artifacts' / 'protocol_layer_proof' / '2026-04-11-recommendation-resolution-window-selective-transition'
BUNDLE_ROOT = REPO_ROOT / 'artifacts' / 'protocol_layer_proof' / '2026-04-11-recommendation-resolution-transition-writeback'


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_json(command: list[str], expected_returncode: int) -> dict:
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != expected_returncode:
        raise RuntimeError(f'unexpected return code {completed.returncode}:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}')
    if completed.stderr.strip():
        raise RuntimeError(completed.stderr)
    return json.loads(completed.stdout)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')


def main() -> int:
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    for path in BUNDLE_ROOT.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)

    for name in [
        'agent_recommendation_2026-04-04.json',
        'agent_recommendation_2026-04-07.json',
        'agent_recommendation_2026-04-10.json',
        'recommendation_judgment_2026-04-04.json',
        'recommendation_judgment_2026-04-10.json',
        'recommendation_resolution_window_before_memory.json',
    ]:
        shutil.copyfile(SEED_ROOT / name, BUNDLE_ROOT / name)

    success_payload = {
        'user_id': 'user_dom',
        'start_date': '2026-04-04',
        'end_date': '2026-04-10',
        'recommendation_artifact_path': str(SEED_ROOT / 'agent_recommendation_2026-04-07.json'),
        'recommendation_artifact_id': 'rec_window_20260407_walk_01',
        'judgment_artifact_path': str(SEED_ROOT / 'recommendation_judgment_2026-04-07.json'),
        'judgment_artifact_id': 'judgment_window_selective_transition_20260407_01',
        'resolution_window_memory_path': str(BUNDLE_ROOT / 'recommendation_resolution_window_before_memory.json'),
        'feedback_window_memory_path': str(SEED_ROOT / 'recommendation_feedback_window_after_memory.json'),
        'written_at': '2026-04-11T14:31:00+01:00',
        'request_id': 'req_resolution_transition_writeback_success_2026_04_11',
        'requested_at': '2026-04-11T14:30:00+01:00',
    }
    rejected_payload = {**success_payload, 'judgment_artifact_id': 'wrong_judgment_id', 'request_id': 'req_resolution_transition_writeback_rejected_2026_04_11'}
    _write_json(BUNDLE_ROOT / 'writeback_success_request.json', success_payload)
    _write_json(BUNDLE_ROOT / 'writeback_rejected_request.json', rejected_payload)

    resolution_before = _run_json([
        sys.executable, '-m', 'health_model.agent_retrieval_cli', 'recommendation-resolution-window',
        '--user-id', 'user_dom', '--start-date', '2026-04-04', '--end-date', '2026-04-10',
        '--memory-locator', str(BUNDLE_ROOT / 'recommendation_resolution_window_before_memory.json'),
        '--request-id', 'req_resolution_before_2026_04_11', '--requested-at', '2026-04-11T14:29:00+01:00',
        '--include-conflicts', 'false', '--include-missingness', 'true'
    ], 0)
    _write_json(BUNDLE_ROOT / 'resolution_window_before.json', resolution_before)

    writeback_success = _run_json([
        sys.executable, '-m', 'health_model.agent_memory_write_cli', 'recommendation-resolution-transition',
        '--output-dir', str(BUNDLE_ROOT), '--payload-path', str(BUNDLE_ROOT / 'writeback_success_request.json')
    ], 0)
    _write_json(BUNDLE_ROOT / 'writeback_success_envelope.json', writeback_success)

    resolution_after_path = Path(writeback_success['artifact_path'])
    resolution_after = _run_json([
        sys.executable, '-m', 'health_model.agent_retrieval_cli', 'recommendation-resolution-window',
        '--user-id', 'user_dom', '--start-date', '2026-04-04', '--end-date', '2026-04-10',
        '--memory-locator', str(resolution_after_path),
        '--request-id', 'req_resolution_after_2026_04_11', '--requested-at', '2026-04-11T14:32:00+01:00',
        '--include-conflicts', 'false', '--include-missingness', 'true'
    ], 0)
    _write_json(BUNDLE_ROOT / 'resolution_window_after.json', resolution_after)

    feedback_after_path = Path(writeback_success['writeback']['written_locator_artifacts']['feedback_window']['artifact_path'])
    feedback_after = _run_json([
        sys.executable, '-m', 'health_model.agent_retrieval_cli', 'recommendation-feedback-window',
        '--user-id', 'user_dom', '--start-date', '2026-04-04', '--end-date', '2026-04-10',
        '--memory-locator', str(feedback_after_path),
        '--request-id', 'req_feedback_after_2026_04_11', '--requested-at', '2026-04-11T14:33:00+01:00'
    ], 0)
    _write_json(BUNDLE_ROOT / 'feedback_window_after.json', feedback_after)

    before_rejection = {
        'dated_artifact_path': writeback_success['artifact_path'],
        'latest_artifact_path': writeback_success['latest_artifact_path'],
        'dated_sha256': _sha256(Path(writeback_success['artifact_path'])),
        'latest_sha256': _sha256(Path(writeback_success['latest_artifact_path'])),
    }
    writeback_rejected = _run_json([
        sys.executable, '-m', 'health_model.agent_memory_write_cli', 'recommendation-resolution-transition',
        '--output-dir', str(BUNDLE_ROOT), '--payload-path', str(BUNDLE_ROOT / 'writeback_rejected_request.json')
    ], 1)
    _write_json(BUNDLE_ROOT / 'writeback_rejected_envelope.json', writeback_rejected)
    after_rejection = {
        'dated_sha256': _sha256(Path(writeback_success['artifact_path'])),
        'latest_sha256': _sha256(Path(writeback_success['latest_artifact_path'])),
    }
    _write_json(BUNDLE_ROOT / 'non_mutation_proof.json', {
        'proof': 'rejected_transition_does_not_mutate_written_locator_artifacts',
        'error_code': writeback_rejected['error']['code'],
        'artifact_state_before_rejection': before_rejection,
        'artifact_state_after_rejection': after_rejection,
        'dated_artifact_unchanged': before_rejection['dated_sha256'] == after_rejection['dated_sha256'],
        'latest_artifact_unchanged': before_rejection['latest_sha256'] == after_rejection['latest_sha256'],
    })

    before_items = {item['date']: item for item in resolution_before['retrieval']['evidence']['per_recommendation']}
    after_items = {item['date']: item for item in resolution_after['retrieval']['evidence']['per_recommendation']}
    _write_json(BUNDLE_ROOT / 'neighbor_stability_proof.json', {
        'proof': 'selective_neighbor_stability',
        'changed_dates': [date for date in sorted(after_items) if before_items.get(date) != after_items.get(date)],
        'expected_changed_date': '2026-04-07',
        'unchanged_judged_neighbor_dates': [
            date for date in ['2026-04-04', '2026-04-10'] if before_items.get(date) == after_items.get(date)
        ],
        'no_recommendation_gaps_after': sorted(gap['date'] for gap in resolution_after['retrieval']['important_gaps']),
    })

    _write_json(BUNDLE_ROOT / 'proof_manifest.json', {
        'date': '2026-04-11',
        'slice': 'protocol_proof.recommendation_resolution_transition_writeback',
        'frozen_command': 'python3 scripts/run_recommendation_resolution_transition_writeback_proof.py',
        'deterministic_replay_commands': [
            'python3 scripts/run_recommendation_resolution_transition_writeback_proof.py',
            'python3 -m health_model.agent_memory_write_cli recommendation-resolution-transition --output-dir artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition-writeback --payload-path artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition-writeback/writeback_success_request.json'
        ],
        'deterministic_replay_tests': [
            'python3 -m unittest tests.test_agent_memory_write_cli tests.test_agent_contract_cli'
        ],
        'smoke_checks': [
            'pre-write window shows the 2026-04-07 target as pending_judgment',
            'successful transition returns ok=true and explicit written locator paths',
            'post-write resolution shows only the target item moving to judged',
            'post-write feedback exposes the linked recommendation plus judgment pair for 2026-04-07',
            'neighbor judged entries remain field-stable and no-recommendation gaps remain unchanged',
            'rejected transition fails closed and does not mutate written locator artifacts'
        ]
    })
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
