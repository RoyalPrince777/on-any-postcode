from mission_control import offline_routing


def test_offline_routing_stays_purple_without_runtime_package(monkeypatch):
    monkeypatch.delenv("OAP_OFFLINE_ROUTING_ENABLED", raising=False)
    monkeypatch.delenv("OAP_OFFLINE_ROUTING_DATASET_ROOT", raising=False)
    monkeypatch.delenv("OAP_OFFLINE_ROUTING_PREFIX", raising=False)

    state = offline_routing.status()

    assert state["offline_local_routing_package_proven"] is False
    assert state["network_required_for_proof"] is False


def test_offline_routing_turns_green_only_with_complete_nonempty_package(monkeypatch, tmp_path):
    prefix = "greater-london"
    for suffix in offline_routing.REQUIRED_SUFFIXES:
        (tmp_path / f"{prefix}{suffix}").write_bytes(b"oap")

    monkeypatch.setenv("OAP_OFFLINE_ROUTING_ENABLED", "true")
    monkeypatch.setenv("OAP_OFFLINE_ROUTING_DATASET_ROOT", str(tmp_path))
    monkeypatch.setenv("OAP_OFFLINE_ROUTING_PREFIX", prefix)

    state = offline_routing.status()

    assert state["offline_local_routing_package_proven"] is True
    assert state["package_present"] is True
    assert state["missing_required_files"] == ()
    assert state["package_bytes"] > 0
    assert len(state["package_fingerprint_sha256"]) == 64


def test_offline_routing_rejects_relative_dataset_root(monkeypatch):
    monkeypatch.setenv("OAP_OFFLINE_ROUTING_ENABLED", "true")
    monkeypatch.setenv("OAP_OFFLINE_ROUTING_DATASET_ROOT", "relative/path")
    monkeypatch.setenv("OAP_OFFLINE_ROUTING_PREFIX", "greater-london")

    state = offline_routing.status()

    assert state["dataset_root_configured"] is False
    assert state["offline_local_routing_package_proven"] is False
