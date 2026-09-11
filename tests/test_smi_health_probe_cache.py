import threading
import time

from mission_control import smi_chat_runtime as runtime


def _patch_health_dependencies(monkeypatch, core_health):
    monkeypatch.setattr(runtime._core, "health", core_health)
    monkeypatch.setattr(runtime._inference, "status", lambda *, probe: {"ready": probe})
    monkeypatch.setattr(runtime._thinking, "validate", lambda: {"valid": True})
    monkeypatch.setattr(runtime, "canonical_memory_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "governed_memory_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "memory_sync_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "_health_probe_running", False)
    monkeypatch.setattr(runtime, "_health_probe_generation", 0)
    monkeypatch.setattr(runtime, "_health_probe_result", None)


def test_overlapping_health_checks_share_one_deep_probe(monkeypatch):
    calls = {"core": 0}
    started = threading.Event()
    release = threading.Event()

    def core_health():
        calls["core"] += 1
        started.set()
        release.wait(timeout=2)
        return {"checks": {"identity": True}}

    _patch_health_dependencies(monkeypatch, core_health)
    results = []

    first = threading.Thread(target=lambda: results.append(runtime.health()))
    second = threading.Thread(target=lambda: results.append(runtime.health()))
    first.start()
    assert started.wait(timeout=1)
    second.start()
    time.sleep(0.02)
    release.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert len(results) == 2
    assert all(item["checks"]["identity"] is True for item in results)
    assert calls["core"] == 1


def test_later_health_check_reprobes_for_fresh_truth(monkeypatch):
    calls = {"core": 0}

    def core_health():
        calls["core"] += 1
        return {"checks": {"identity": calls["core"] > 1}}

    _patch_health_dependencies(monkeypatch, core_health)

    first = runtime.health()
    second = runtime.health()

    assert first["checks"]["identity"] is False
    assert second["checks"]["identity"] is True
    assert calls["core"] == 2
