from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_founder_surface_retains_core_chat_controls():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    for element_id in (
        'id="chat-form"', 'id="message"', 'id="plus-button"',
        'id="image-button"', 'id="file-button"', 'id="code-button"',
        'id="speaker-button"', 'id="mic-button"', 'id="stop-button"',
        'id="send"', 'id="history-list"',
    ):
        assert element_id in base


def test_founder_surface_supports_media_and_documents():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    for extension in (".pdf", ".txt", ".md", ".csv", ".json", ".docx", ".pptx", ".xlsx"):
        assert extension in base
    assert "audio/mpeg" in base
    assert "video/mp4" in base
