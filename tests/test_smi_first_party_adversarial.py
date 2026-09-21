"""P0 application-level private inference isolation checks.

These intercept selected Python call sites, not an OS or hosted-network egress
firewall. They do not certify hosted custody, HRM persistence, or production.
"""
from __future__ import annotations

import json

import pytest

from mission_control import oap_inference_gateway as gateway
from mission_control import smi_cancellation, smi_chat_runtime


def _reject_external(*args, **kwargs):
    raise AssertionError("external_inference_or_telemetry_attempt")


@pytest.mark.parametrize("local_up,bridge_up", [(False, False), (False, True), (True, False)])
def test_private_text_never_calls_external_provider(monkeypatch, local_up, bridge_up):
    calls = []
    deltas = []

    def local(*args, **kwargs):
        calls.append("local")
        if not local_up:
            raise RuntimeError("local_unavailable")
        return "local_answer"

    def bridge(*args, **kwargs):
        calls.append("bridge")
        if not bridge_up:
            raise RuntimeError("bridge_unavailable")
        return "bridge_answer"

    monkeypatch.setattr(gateway, "_call_local", local)
    monkeypatch.setattr(gateway, "_call_bridge", bridge)
    monkeypatch.setattr(gateway, "FALLBACK_ENABLED", True)
    monkeypatch.setattr(smi_chat_runtime, "_COMPATIBILITY_ENGINE", _reject_external)
    monkeypatch.setattr(smi_chat_runtime._core, "urlrequest", object())

    if not local_up and not bridge_up:
        with pytest.raises(RuntimeError, match="first_party_inference_required"):
            smi_chat_runtime._gateway_provider("private context", on_delta=deltas.append)
        assert deltas == []
        assert calls == ["local", "bridge"]
    else:
        result = smi_chat_runtime._gateway_provider(
            "private context", on_delta=deltas.append
        )
        assert result == ("local_answer" if local_up else "bridge_answer")
        assert deltas == [result]
        assert calls == (["local"] if local_up else ["local", "bridge"])


def test_private_gateway_denies_outbound_when_both_first_party_paths_fail(monkeypatch):
    calls = []

    def fail_local(*args, **kwargs):
        calls.append("local")
        raise RuntimeError("local_down")

    def fail_bridge(*args, **kwargs):
        calls.append("bridge")
        raise RuntimeError("bridge_down")

    monkeypatch.setattr(gateway, "_call_local", fail_local)
    monkeypatch.setattr(gateway, "_call_bridge", fail_bridge)
    monkeypatch.setattr(gateway, "FALLBACK_ENABLED", True)
    monkeypatch.setattr(smi_chat_runtime, "_COMPATIBILITY_ENGINE", _reject_external)
    monkeypatch.setattr(smi_chat_runtime._core.urlrequest, "urlopen", _reject_external)
    with pytest.raises(RuntimeError, match="first_party_inference_required"):
        smi_chat_runtime._gateway_provider("Founder HRM private context")
    assert calls == ["local", "bridge"]


def test_local_inference_uses_loopback_opener_not_global_http(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"message": {"content": "local_only"}}).encode()

    class Opener:
        def open(self, request, timeout):
            assert request.full_url == "http://127.0.0.1:11434/api/chat"
            assert timeout == 2.0
            return Response()

    monkeypatch.setattr(gateway, "LOCAL_URL", "http://127.0.0.1:11434/api/chat")
    monkeypatch.setattr(gateway, "LOCAL_ENABLED", True)
    monkeypatch.setattr(gateway, "_LOCAL_OPENER", Opener())
    monkeypatch.setattr(gateway.urlrequest, "urlopen", _reject_external)
    assert smi_chat_runtime._gateway_provider("private") == "local_only"


def test_private_image_does_not_use_local_or_external_text_only_route(monkeypatch):
    monkeypatch.setattr(gateway, "FALLBACK_ENABLED", True)
    monkeypatch.setattr(gateway, "_call_local", _reject_external)
    monkeypatch.setattr(gateway, "_call_bridge", _reject_external)
    monkeypatch.setattr(smi_chat_runtime, "_COMPATIBILITY_ENGINE", _reject_external)
    with pytest.raises(RuntimeError, match="first_party_inference_required"):
        smi_chat_runtime._gateway_provider(
            "analyse private image", image_data="data:image/png;base64,YQ=="
        )


def test_stop_before_bridge_does_not_emit_answer_or_call_raw_provider(monkeypatch):
    token = smi_cancellation.new_token("founder")
    deltas = []

    def stopped_local(*args, **kwargs):
        token.cancel("human_stop")
        token.raise_if_cancelled()

    monkeypatch.setattr(gateway, "_call_local", stopped_local)
    monkeypatch.setattr(gateway, "_call_bridge", _reject_external)
    monkeypatch.setattr(smi_chat_runtime, "_COMPATIBILITY_ENGINE", _reject_external)
    with pytest.raises(smi_cancellation.SMIRequestCancelled):
        smi_chat_runtime._gateway_provider(
            "private", cancellation_token=token, on_delta=deltas.append
        )
    assert deltas == []


def test_source_hrm_write_is_after_provider_success():
    """Ordering proof only; separate real-DB failure/rollback proof is required."""
    from pathlib import Path

    core = (
        Path(__file__).resolve().parents[1]
        / "mission_control"
        / "smi_chat_runtime_core.py"
    ).read_text()
    provider = core.index("response = _provider(")
    complete = core.index("provider_completed = True", provider)
    memory = core.index("INSERT INTO smi_memory_records", complete)
    commit = core.index("_commit_if_not_cancelled(connection, cancellation_token)", memory)
    assert provider < complete < memory < commit
