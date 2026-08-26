import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "scripts" / "termux_home_node_run.sh").read_text()
SETUP = (ROOT / "scripts" / "termux_home_node_setup.sh").read_text()
STATUS = (ROOT / "scripts" / "termux_home_node_status.sh").read_text()
DOC = (ROOT / "docs" / "TERMUX_HOME_NODE.md").read_text()
TERMUX_REQUIREMENTS = (ROOT / "requirements-termux-home-node.txt").read_text()
MISSION_INIT = (ROOT / "mission_control" / "__init__.py").read_text()


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


def test_termux_setup_uses_minimal_android_worker_requirements():
    active_requirements = [
        line.strip().casefold()
        for line in TERMUX_REQUIREMENTS.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert "pkg install -y python git postgresql" in SETUP
    assert "requirements-termux-home-node.txt" in SETUP
    assert "requirements.txt" not in SETUP
    assert "PSYCOPG_IMPL=python" in SETUP
    assert "pq.__impl__" in SETUP
    assert "cryptography" in SETUP
    assert any(line.startswith("psycopg") for line in active_requirements)
    assert all("binary" not in line for line in active_requirements)
    assert all("pyjwt" not in line for line in active_requirements)
    assert all("cryptography" not in line for line in active_requirements)


def test_mission_control_package_keeps_web_imports_out_of_worker_import_path():
    tree = ast.parse(MISSION_INIT)
    top_level_imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_imports.append(node.module)
    assert "flask" not in top_level_imports
    assert "click" not in top_level_imports
    assert "from .views import bp" in MISSION_INIT
    assert MISSION_INIT.index("def init_app") < MISSION_INIT.index("from .views import bp")


def test_termux_status_uses_authoritative_runtime_readiness():
    assert "runtime_status" in STATUS
    assert "home_node_process=" in STATUS
    assert '"worker_fresh": true' in DOC
    assert '"ready": true' in DOC


def test_termux_documentation_preserves_human_authority_boundary():
    assert "Human Authority" in DOC
    assert "does **not** auto-pull" in DOC
    assert "consequential execution disabled" in DOC
