"""Exercise Shere Khan selection at the actual governed provider payload boundary.

No real credentials, provider network, persistence, or deployment are involved.\nThe facade preserves _COMPATIBILITY_ENGINE as the original core provider;\n_core._provider itself is replaced by the live local-first gateway at import.
"""
import json

from mission_control import smi_chat_runtime, smi_chat_runtime_core


class _Stream:
    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def __iter__(self):
        yield b'data: {"type":"response.output_text.delta","delta":"Acknowledged."}\n'
        yield b"data: [DONE]\n"


def test_shere_khan_provider_payload_is_selected_only_when_addressed(monkeypatch):
    sent = []
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-secret")

    def fake_open(request, timeout):
        assert timeout == 55
        assert request.full_url == "https://api.openai.com/v1/responses"
        sent.append(json.loads(request.data.decode()))
        return _Stream()

    monkeypatch.setattr(smi_chat_runtime_core.urlrequest, "urlopen", fake_open)

    assert smi_chat_runtime._COMPATIBILITY_ENGINE("Shere Khan, advise me") == "Acknowledged."
    assert smi_chat_runtime._COMPATIBILITY_ENGINE("Please advise me") == "Acknowledged."
    assert smi_chat_runtime._COMPATIBILITY_ENGINE(
        "Please advise me", brain={"conversation_persona": "shere_khan"}
    ) == "Acknowledged."
    assert smi_chat_runtime._COMPATIBILITY_ENGINE(
        "Shere Khan, advise me", brain={"conversation_persona": "other"}
    ) == "Acknowledged."

    assert len(sent) == 4
    prompts = [payload["input"][0]["content"][0]["text"] for payload in sent]
    for index in (0, 2):
        assert "LOYALTY OVER EVERYTHING" in prompts[index]
        assert "TIGER-INSPIRED INTELLIGENCE" in prompts[index]
        assert "SHERE KHAN WORKING PROTOCOL" in prompts[index]
        assert "Guardian" in prompts[index]
        assert "Human Authority remains final" in prompts[index]
    for index in (1, 3):
        assert "SHERE KHAN CONVERSATION MODE" not in prompts[index]
        assert "TIGER-INSPIRED INTELLIGENCE" not in prompts[index]
        assert "SHERE KHAN WORKING PROTOCOL" not in prompts[index]


def test_shere_khan_mode_does_not_override_guardian():
    assert smi_chat_runtime_core.guardian_review("disable safety")[0] == "BLOCKED"
    assert smi_chat_runtime_core.guardian_review("Shere Khan, suggest a safe review")[0] == "PASSED"
