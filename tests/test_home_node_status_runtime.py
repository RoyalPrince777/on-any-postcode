"""Exercise Home Node readiness output with real script execution and isolated inputs."""
from __future__ import annotations

import json
import runpy
import sys
import types
from pathlib import Path


def test_status_rejects_stale_supervisor_heartbeat(monkeypatch, tmp_path: Path, capsys) -> None:
    state_dir = tmp_path / "home-state"
    state_dir.mkdir()
    (state_dir / "workers.json").write_text(json.dumps({
        "supervisor_pid": 1234,
        "organism_pid": 1235,
        "inference_pid": 1236,
        "updated_at": 1,
        "platform": "test",
    }), encoding="utf-8")
    monkeypatch.setenv("OAP_HOME_STATE", str(state_dir))
    monkeypatch.setenv("OAP_HOME_NODE_BRIDGE_SECRET", "x" * 32)
    runtime_module = types.ModuleType("mission_control.organism_runtime")
    runtime_module.runtime_status = lambda: {"ready": True}
    monkeypatch.setitem(sys.modules, "mission_control.organism_runtime", runtime_module)
    monkeypatch.setattr("os.kill", lambda pid, sig: None)
    runpy.run_path("scripts/oap_home_node_status.py", run_name="__main__")
    snapshot = json.loads(capsys.readouterr().out)
    assert snapshot["supervisor_heartbeat_recent"] is False
    assert snapshot["device_ready"] is False
    assert snapshot["home_node_process"] == "running"


def test_status_rejects_non_object_state(monkeypatch, tmp_path: Path, capsys) -> None:
    state_dir = tmp_path / "home-state"
    state_dir.mkdir()
    (state_dir / "workers.json").write_text("[1, 2, 3]", encoding="utf-8")
    monkeypatch.setenv("OAP_HOME_STATE", str(state_dir))
    monkeypatch.setenv("OAP_HOME_NODE_BRIDGE_SECRET", "x" * 32)
    runtime_module = types.ModuleType("mission_control.organism_runtime")
    runtime_module.runtime_status = lambda: {"ready": True}
    monkeypatch.setitem(sys.modules, "mission_control.organism_runtime", runtime_module)
    runpy.run_path("scripts/oap_home_node_status.py", run_name="__main__")
    snapshot = json.loads(capsys.readouterr().out)
    assert snapshot["device_ready"] is False
    assert snapshot["supervisor_heartbeat_recent"] is False
