from mission_control import smi_chat_runtime


def _codes(events):
    return [item.get("code") for item in events if item.get("type") == "error"]


def test_persistence_classifier_recognises_neon_quota_and_connection_failures():
    assert smi_chat_runtime.persistence_unavailable(
        Exception("Data transfer quota exceeded")
    )
    assert smi_chat_runtime.persistence_unavailable(
        Exception("connection refused by server")
    )
    assert smi_chat_runtime.persistence_unavailable(
        Exception("could not connect to server")
    )
    assert smi_chat_runtime.persistence_unavailable(
        Exception("connection timed out")
    )


def test_persistence_classifier_follows_wrapped_causes():
    root = OSError("connection refused")
    wrapped = RuntimeError("governed store unavailable")
    wrapped.__cause__ = root
    assert smi_chat_runtime.persistence_unavailable(wrapped)


def test_chat_events_fail_closed_on_persistence_failure(monkeypatch):
    def fail_chat(*args, **kwargs):
        raise OSError("could not connect to server")

    monkeypatch.setattr(smi_chat_runtime, "chat", fail_chat)
    events = list(smi_chat_runtime.chat_events("status", "founder", "Founder"))

    assert _codes(events) == ["persistence_unavailable"]
    assert not any(item.get("type") == "complete" for item in events)
    message = next(item["message"] for item in events if item.get("type") == "error")
    assert "No completion was recorded" in message


def test_wrapped_runtime_persistence_failure_is_not_mislabelled(monkeypatch):
    def fail_chat(*args, **kwargs):
        root = OSError("connection refused")
        raise RuntimeError("governed store unavailable") from root

    monkeypatch.setattr(smi_chat_runtime, "chat", fail_chat)
    events = list(smi_chat_runtime.chat_events("status", "founder", "Founder"))

    assert _codes(events) == ["persistence_unavailable"]
    assert not any(item.get("type") == "complete" for item in events)


def test_plain_runtime_provider_failure_stays_provider_unavailable(monkeypatch):
    def fail_chat(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(smi_chat_runtime, "chat", fail_chat)
    events = list(smi_chat_runtime.chat_events("status", "founder", "Founder"))

    assert _codes(events) == ["provider_unavailable"]
    assert not any(item.get("type") == "complete" for item in events)


def test_unknown_failure_still_fails_closed(monkeypatch):
    def fail_chat(*args, **kwargs):
        raise Exception("unexpected internal fault")

    monkeypatch.setattr(smi_chat_runtime, "chat", fail_chat)
    events = list(smi_chat_runtime.chat_events("status", "founder", "Founder"))

    assert _codes(events) == ["internal_error"]
    assert not any(item.get("type") == "complete" for item in events)
