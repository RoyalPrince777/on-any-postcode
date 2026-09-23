from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/oap_os_home_node_readiness.py"
spec = importlib.util.spec_from_file_location("oap_os_home_node_readiness", SOURCE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_readiness_fail_closed_without_device_or_repo(tmp_path, monkeypatch):
    monkeypatch.delenv("OAP_HOME_REPO", raising=False)
    result = module.readiness(home=tmp_path, repo=tmp_path / "missing", android_host=False)
    assert result["physical_device_verified"] is False
    assert result["ready_for_device_certification"] is False
    assert result["repository_revision"] is None
    assert result["repo_present"] is False
    assert result["map_road_source"] == "not_checked"
    assert result["device_location_permission"] == "not_checked"
    assert result["read_only"] is True
    assert not (tmp_path / ".config").exists()


def test_readiness_does_not_read_private_env_or_claim_native_os(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "mission_control/static").mkdir(parents=True)
    (repo / "scripts/termux_home_node_run.sh").write_text("existing")
    (repo / "mission_control/static/oap_os_map_bridge.js").write_text("existing")
    secret = tmp_path / ".config/oap/home-node.env"
    secret.parent.mkdir(parents=True)
    secret.write_text("PRIVATE_TEST_SENTINEL")
    result = module.readiness(home=tmp_path, repo=repo, android_host=True)
    assert result["host"] == "android_termux"
    assert result["private_env_present"] is True
    assert result["worker_runner_present"] is True
    assert result["map_runtime_bridge_present"] is True
    assert result["custom_android_os"] is False
    assert result["native_apk"] is False
    assert "PRIVATE_TEST_SENTINEL" not in str(result)
    assert result["ready_for_device_certification"] is False


def test_readiness_source_does_not_change_phone_or_run_worker():
    source = SOURCE.read_text()
    for forbidden in (
        "git pull", "git clone", "pkg install", "adb ", "su -c",
        "termux-location", "termux-wake-lock", "source \"$ENV_FILE\"",
        "requests.get", "urlopen(", "chmod(", "mkdir(", "write_text(",
    ):
        assert forbidden not in source
    assert "subprocess.run(" in source
    assert '"rev-parse", "--verify", "HEAD"' in source
