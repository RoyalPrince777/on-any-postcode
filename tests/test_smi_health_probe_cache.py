from mission_control import smi_chat_runtime as runtime


def test_health_reuses_recent_deep_probe(monkeypatch):
    calls = {"core": 0, "inference": 0}

    def core_health():
        calls["core"] += 1
        return {"checks": {"identity": True}}

    def inference_status(*, probe):
        assert probe is True
        calls["inference"] += 1
        return {"ready": True}

    monkeypatch.setattr(runtime._core, "health", core_health)
    monkeypatch.setattr(runtime._inference, "status", inference_status)
    monkeypatch.setattr(runtime._thinking, "validate", lambda: {"valid": True})
    monkeypatch.setattr(runtime, "canonical_memory_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "governed_memory_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "memory_sync_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "_health_cache", None)
    monkeypatch.setattr(runtime, "_health_cache_at", 0.0)

    first = runtime.health()
    second = runtime.health()

    assert first["checks"]["identity"] is True
    assert second["checks"]["identity"] is True
    assert calls == {"core": 1, "inference": 1}


def test_health_force_bypasses_cache(monkeypatch):
    calls = {"core": 0}

    def core_health():
        calls["core"] += 1
        return {"checks": {"identity": True}}

    monkeypatch.setattr(runtime._core, "health", core_health)
    monkeypatch.setattr(runtime._inference, "status", lambda *, probe: {"ready": probe})
    monkeypatch.setattr(runtime._thinking, "validate", lambda: {"valid": True})
    monkeypatch.setattr(runtime, "canonical_memory_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "governed_memory_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "memory_sync_status", lambda: {"ready": True})
    monkeypatch.setattr(runtime, "_health_cache", None)
    monkeypatch.setattr(runtime, "_health_cache_at", 0.0)

    runtime.health()
    runtime.health(force=True)

    assert calls["core"] == 2
