from __future__ import annotations

from mission_control import status


def test_ollama_unavailable_is_degraded_without_crashing(client, monkeypatch):
    monkeypatch.setattr(status, "_probe_ollama", lambda: False)

    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Ollama" in page
    assert "Degraded" in page
