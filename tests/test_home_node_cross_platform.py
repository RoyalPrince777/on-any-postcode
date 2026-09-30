from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = (ROOT / "scripts" / "oap_home_node_supervisor.py").read_text(encoding="utf-8")
STATUS = (ROOT / "scripts" / "oap_home_node_status.py").read_text(encoding="utf-8")
POSIX = (ROOT / "scripts" / "home_node_run.sh").read_text(encoding="utf-8")
WINDOWS = (ROOT / "scripts" / "home_node_run.ps1").read_text(encoding="utf-8")
DOC = (ROOT / "docs" / "HOME_NODE.md").read_text(encoding="utf-8")


def test_cross_platform_supervisor_runs_both_bounded_workers():
    assert "mission_control.organism_worker" in SUPERVISOR
    assert "oap_home_node_inference_worker.py" in SUPERVISOR
    assert "OAP_HOME_NODE_BRIDGE_SECRET" in SUPERVISOR
    assert "OAP_NEON_DATABASE_URL" in SUPERVISOR
    assert "subprocess.Popen" in SUPERVISOR
    assert "deploy" not in SUPERVISOR.casefold()
    assert "payment" not in SUPERVISOR.casefold()


def test_linux_macos_and_windows_launch_same_supervisor():
    assert "oap_home_node_supervisor.py" in POSIX
    assert "oap_home_node_supervisor.py" in WINDOWS
    assert ".venv/bin/python" in POSIX
    assert ".venv\\Scripts\\python.exe" in WINDOWS


def test_canonical_status_requires_both_workers_and_runtime_readiness():
    assert '"home_node_process"' in STATUS
    assert '"organism_worker"' in STATUS
    assert '"inference_worker"' in STATUS
    assert '"bridge_secret_configured"' in STATUS
    assert '"device_ready"' in STATUS
    assert 'snapshot["organism_runtime"].get("ready")' in STATUS


def test_home_node_role_is_device_agnostic_and_governed():
    for phrase in (
        "Android phone or tablet",
        "Linux desktop or laptop",
        "macOS desktop or laptop",
        "Windows desktop or laptop",
        "worker_recently_seen=true",
        "first_party_inference_ready=true",
        "Human Authority remains final",
        "consequential execution disabled",
    ):
        assert phrase in DOC
    assert "does not self-update" in DOC.casefold()
