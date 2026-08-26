from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "scripts" / "termux_home_node_run.sh").read_text()
SETUP = (ROOT / "scripts" / "termux_home_node_setup.sh").read_text()
STATUS = (ROOT / "scripts" / "termux_home_node_status.sh").read_text()
DOC = (ROOT / "docs" / "TERMUX_HOME_NODE.md").read_text()


def test_termux_runner_uses_existing_bounded_worker_without_self_updating():
    assert "mission_control.organism_worker" in RUNNER
    assert "termux-wake-lock" in RUNNER
    assert "git pull" not in RUNNER
    assert "git fetch" not in RUNNER
    assert "deploy" not in RUNNER.casefold()
    assert "payment" not in RUNNER.casefold()
    assert "dispatch" not in RUNNER.casefold()


def test_termux_setup_keeps_database_secret_out_of_repository():
    assert "read -r -s database_url" in SETUP
    assert "$HOME/.config/oap" in SETUP
    assert "chmod 600" in SETUP
    assert "OAP_NEON_DATABASE_URL" in SETUP
    assert "postgresql://neondb_owner:" not in SETUP


def test_termux_status_uses_authoritative_runtime_readiness():
    assert "runtime_status" in STATUS
    assert "home_node_process=" in STATUS
    assert '"worker_fresh": true' in DOC
    assert '"ready": true' in DOC


def test_termux_documentation_preserves_human_authority_boundary():
    assert "Human Authority" in DOC
    assert "does not auto-pull" in DOC
    assert "consequential execution disabled" in DOC
