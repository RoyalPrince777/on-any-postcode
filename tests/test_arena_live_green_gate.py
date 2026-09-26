from __future__ import annotations

import scripts.arena_live_green_gate as gate


class _Response:
    status = 200

    def __init__(self, body: str):
        self._body = body.encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _body(*, omit: str | None = None) -> str:
    return "\n".join(marker for marker in gate.REQUIRED_MARKERS if marker != omit)


def test_probe_accepts_200_with_required_arena_markers(monkeypatch):
    monkeypatch.setattr(gate.request, "urlopen", lambda *_a, **_k: _Response(_body()))
    result = gate.probe()
    assert result["ok"] is True
    assert result["status"] == 200
    assert result["missing_markers"] == []


def test_probe_fails_closed_when_global_marker_missing(monkeypatch):
    monkeypatch.setattr(
        gate.request,
        "urlopen",
        lambda *_a, **_k: _Response(_body(omit="Global Arena")),
    )
    result = gate.probe()
    assert result["ok"] is False
    assert "Global Arena" in result["missing_markers"]
