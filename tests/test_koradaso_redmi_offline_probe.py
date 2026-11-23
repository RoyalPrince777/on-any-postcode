"""Network-free tests for the fixed-loopback Redmi offline AI probe."""
import io
import json

import pytest

from scripts import koradaso_redmi_offline_probe as probe


class FakeOpener:
    def __init__(self, tags, chat=None):
        self.tags = tags
        self.chat = chat
        self.calls = []

    def open(self, req, timeout=None):
        self.calls.append((req.full_url, req.get_method(), timeout))
        if req.full_url == probe._TAGS:
            return io.BytesIO(json.dumps(self.tags).encode())
        assert req.full_url == probe._CHAT
        return io.BytesIO(json.dumps(self.chat).encode())


def test_local_only_inference_returns_proof_not_answer():
    client = FakeOpener(
        {"models": [{"name": "smallsmi:latest"}]},
        {"message": {"content": "LOCAL OK"}},
    )
    report = probe.probe_local("smallsmi:latest", opener=client)
    assert report["status"] == "local_inference_passed"
    assert report["production_ready"] is False
    assert report["airplane_mode_independently_verified"] is False
    assert "LOCAL OK" not in str(report)
    assert client.calls[0][:2] == (probe._TAGS, "GET")
    assert client.calls[1][:2] == (probe._CHAT, "POST")
    assert all(x[0].startswith("http://127.0.0.1:11434/") for x in client.calls)


def test_no_model_cannot_fake_success():
    client = FakeOpener({"models": []})
    report = probe.probe_local("not-installed", opener=client)
    assert report == {
        "status": "not_ready", "reason": "model_not_installed", "local_only": True
    }
    assert len(client.calls) == 1


@pytest.mark.parametrize("name", ["", "bad model", "bad\nname", "a" * 161])
def test_invalid_model_fails_before_any_network(name):
    client = FakeOpener({"models": [{"name": name}]})
    with pytest.raises(ValueError, match="invalid_local_model_name"):
        probe.probe_local(name, opener=client)
    assert client.calls == []


def test_malformed_local_responses_fail_closed():
    client = FakeOpener(["unexpected"])
    assert probe.probe_local("smallsmi", opener=client)["status"] == "not_ready"
    client = FakeOpener(
        {"models": [{"name": "smallsmi"}]}, {"unexpected": "response"}
    )
    report = probe.probe_local("smallsmi", opener=client)
    assert report["status"] == "not_ready"
    client = FakeOpener(
        {"models": [{"name": "smallsmi"}]}, ["unexpected"]
    )
    assert probe.probe_local("smallsmi", opener=client)["status"] == "not_ready"


def test_timeout_bounds():
    with pytest.raises(ValueError, match="timeout_out_of_bounds"):
        probe.probe_local("smallsmi", timeout=121)
