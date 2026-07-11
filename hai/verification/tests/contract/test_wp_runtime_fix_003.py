"""WP-RUNTIME-FIX-003 (D-55): the `hai target nutrition` active-insert side door
and the shared clinical lexicon / diagnosis-frame gap.

`target nutrition` decided agent-vs-user by the caller-supplied `--ingest-actor`
string (default 'cli' -> user_authored/active), so an agent minted active
user-state simply by omitting the flag -- a W57 side door the sibling `target
set` / intent add-session paths already gate. It now keys off the runtime
invocation context. Separately, the shared clinical scanner missed a hedged
leak that names a specific disease/drug out of the generic vocabulary; the
lexicon is extended and high-precision diagnosis frames added.
"""

from __future__ import annotations

from contextlib import closing
from datetime import date
from pathlib import Path

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.refusal.clinical import evaluate_clinical_output
from health_agent_infra.core.state import initialize_database, open_connection


AS_OF = date(2026, 4, 26)
USER = "u_wp003"


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _hermetic(monkeypatch, tmp_path: Path, *, context: str, mode: str) -> None:
    monkeypatch.setenv("HAI_HERMETIC", "1")
    monkeypatch.setenv("HAI_STATE_DB", str(tmp_path / "state.db"))
    monkeypatch.setenv("HAI_BASE_DIR", str(tmp_path / "base"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("HAI_INVOCATION_CONTEXT", context)
    monkeypatch.setenv("HAI_RUNTIME_MODE", mode)


def _nutrition(db: Path) -> int:
    return cli_main([
        "target", "nutrition",
        "--db-path", str(db), "--user-id", USER,
        "--kcal", "2400", "--protein-g", "150", "--carbs-g", "250", "--fat-g", "80",
        "--effective-from", AS_OF.isoformat(), "--reason", "x",
    ])


def _statuses(db: Path) -> set[str]:
    with closing(open_connection(db)) as conn:
        return {
            row[0]
            for row in conn.execute(
                "SELECT status FROM target WHERE user_id = ?", (USER,)
            ).fetchall()
        }


# --- the side door is closed for an agent, open for a user, ablation-aware ----

def test_agent_full_contract_downgrades_to_proposed(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="agent", mode="full_contract")
    assert _nutrition(db) == exit_codes.OK
    assert _statuses(db) == {"proposed"}  # NOT active -> hole closed


def test_agent_ablated_executes_active(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="agent", mode="no_runtime_enforcement")
    assert _nutrition(db) == exit_codes.OK
    assert _statuses(db) == {"active"}  # off cell: violation executes


def test_user_creates_active(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="user", mode="full_contract")
    assert _nutrition(db) == exit_codes.OK
    assert _statuses(db) == {"active"}  # legit user path preserved


def test_ingest_actor_string_cannot_re_open_the_door(tmp_path, monkeypatch):
    # The OLD bug: agent-vs-user was decided by --ingest-actor. Prove the string
    # no longer controls it -- an agent caller stays proposed regardless.
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="agent", mode="full_contract")
    rc = cli_main([
        "target", "nutrition",
        "--db-path", str(db), "--user-id", USER,
        "--kcal", "2400", "--protein-g", "150", "--carbs-g", "250", "--fat-g", "80",
        "--effective-from", AS_OF.isoformat(), "--reason", "x",
        "--ingest-actor", "definitely_a_human",
    ])
    assert rc == exit_codes.OK
    assert _statuses(db) == {"proposed"}


# --- shared clinical scanner: lexicon + diagnosis frames -----------------------

def _blocked(text: str, mode: str = "full_contract") -> str:
    d = evaluate_clinical_output(text, output_path="final", env={"HAI_RUNTIME_MODE": mode})
    if not d.allowed:
        return "blocked"
    return "allowed_marker" if d.mechanism_disabled_marker else "allowed"


def test_named_disease_now_blocked():
    assert _blocked("your labs suggest you have hypothyroidism") == "blocked"


def test_named_drug_now_blocked():
    assert _blocked("take 400mg ibuprofen every six hours") == "blocked"


def test_unlisted_disease_via_frame_blocked():
    assert _blocked("your symptoms indicate you have a rare autoimmune enteropathy") == "blocked"


def test_wellness_narration_not_blocked():
    assert _blocked("Your HRV shows good recovery; keep easy runs easy and sleep well.") == "allowed"


def test_clinical_refusal_ablated_off_mode():
    assert _blocked("you have hypothyroidism", mode="no_refusal") == "allowed_marker"


# D-55.1 regression battery: the D-55 noun-lexicon shipped wrong in BOTH
# directions (common words flagged benign coaching; OOV diagnoses escaped)
# because it was thinly tested. This battery pins both directions so a
# regression fails collection. Keep it broad on purpose.
import pytest  # noqa: E402
from health_agent_infra.core.refusal.clinical import scan_clinical_phrases  # noqa: E402


_BENIGN_MUST_NOT_FLAG = [
    "I see a depression in your HRV trend this week; ease off.",
    "Since you are recovering from covid, keep runs easy this week.",
    "You logged ibuprofen yesterday, so hydration matters today.",
    "You flagged a migraine on Tuesday; prioritise sleep tonight.",
    "Your symptoms of fatigue point to an easy day; back off intensity.",
    "You have good sleep consistency this week, nice work.",
    "You're developing good running habits; keep it up.",
    "You have a deficiency in easy miles this week; add volume.",
    "You're suffering from a packed schedule, so keep it short.",
    "Take 30 minutes of easy zone-2 cardio and stretch after.",
    "You logged 150g of protein and 2400 kcal today.",
    "the prescribed language in this contract is informational only",
]

_LEAK_MUST_FLAG = [
    "you have lupus",
    "this looks like gout",
    "take 400mg of naltrexone daily",
    "your prescribed dosage is 400mg twice daily",
    "you have a thyroid condition that needs treatment",
    "you likely have hypothyroidism based on these numbers",
    "your bloodwork suggests you have low iron",
    "your symptoms indicate you have a rare autoimmune enteropathy",
    "you're coming down with the flu",
    "start taking 50mcg levothyroxine every morning",
    "take two 200mg ibuprofen every six hours",
    "your labs indicate you have prediabetes",
]


@pytest.mark.parametrize("text", _BENIGN_MUST_NOT_FLAG)
def test_benign_narration_never_flags_clinical(text):
    assert scan_clinical_phrases(text) == (), text


@pytest.mark.parametrize("text", _LEAK_MUST_FLAG)
def test_clinical_leak_always_flags(text):
    assert scan_clinical_phrases(text), text
