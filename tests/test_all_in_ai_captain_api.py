import json

import pytest

from mission_control import all_in_ai_captain_api as captain


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def test_captain_status_keeps_authority_boundary(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    state = captain.status()
    assert state["name"] == "ALL IN A.I."
    assert state["role"] == "Captain Agent"
    assert state["reports_to"] == "SMI"
    assert state["founder_final"] is True
    assert state["responses_api"] is True
    assert state["web_search"] is True
    assert state["configured"] is True
    assert state["mission_status"]["percentage"] == 86
    assert state["mission_status"]["passed"] == 6
    assert state["mission_status"]["total"] == 7
    assert state["mission_status"]["green"] is False
    assert state["mission_status"]["stages"]["live_provider_proof"] is False
    assert state["mission_status"]["cosmetic_inflation"] is False
    assert "not the ChatGPT app session" in state["truth_boundary"]


def test_captain_requires_message():
    with pytest.raises(ValueError, match="captain_message_required"):
        captain.ask("")


def test_captain_uses_responses_api_and_extracts_sources(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["auth"] = req.headers.get("Authorization")
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "id": "resp_test",
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Captain answer",
                                "annotations": [
                                    {
                                        "type": "url_citation",
                                        "title": "OpenAI",
                                        "url": "https://openai.com/",
                                    }
                                ],
                            }
                        ]
                    }
                ],
            }
        )

    monkeypatch.setattr(captain.urlrequest, "urlopen", fake_urlopen)
    result = captain.ask("Find current information")

    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["auth"] == "Bearer test-key"
    assert captured["timeout"] == 55
    assert captured["body"]["tools"] == [{"type": "web_search"}]
    system = captured["body"]["input"][0]["content"][0]["text"]
    assert "Never call yourself SMI" in system
    assert "Queen Bee" in system
    assert "Swarm" in system
    assert "Spider" in system
    assert "Shere Khan" in system
    assert "Octopus" in system
    assert "Fox" in system
    assert result["answer"] == "Captain answer"
    assert result["sources"][0]["url"] == "https://openai.com/"
    assert result["execution_granted"] is False
    assert result["founder_final"] is True
    assert result["mission_status"]["percentage"] == 100
    assert result["mission_status"]["green"] is True
    assert result["mission_status"]["stages"]["live_provider_proof"] is True
