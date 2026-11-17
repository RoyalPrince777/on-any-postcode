from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = (ROOT / "scripts/termux_core_setup.sh").read_text()
REQUIREMENTS = (ROOT / "requirements-termux-core.txt").read_text()
LAUNCHER = (ROOT / "scripts/smi_local_flask.sh").read_text()


def test_core_environment_does_not_modify_existing_worker_or_start_automatically():
    assert "requirements-termux-core.txt" in SETUP
    assert "requirements-termux-home-node.txt" not in SETUP
    assert ".venv-core/bin/python" in SETUP
    assert "python -m venv .venv-core" in SETUP
    assert "OAP_CORE_PYTHON" in SETUP
    assert "smi_local_flask.sh" in SETUP
    assert "git pull" not in SETUP
    assert "git fetch" not in SETUP
    assert "termux_home_node_run.sh" not in SETUP
    assert "app.run(" not in SETUP
    assert "docker" not in SETUP
    assert "onrender.com" not in SETUP


def test_android_web_dependencies_are_separate_and_preserve_crypto():
    assert "psycopg[binary]" not in REQUIREMENTS
    assert "psycopg>=3.2,<4" in REQUIREMENTS
    assert "PyJWT[crypto]" in REQUIREMENTS
    assert "espeak-english" in REQUIREMENTS
    assert "OAP_CORE_IMPORT_PREFLIGHT_PASSED" in SETUP
    assert "OAP_CORE_DEPENDENCIES_MISSING" in LAUNCHER
    assert 'host="127.0.0.1", port=port' in LAUNCHER
