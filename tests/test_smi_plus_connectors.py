from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
BASE = ROOT / "mission_control" / "templates" / "ollama_chat_base.html"


def test_plus_is_single_connected_tools_and_attachment_entry():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    base = BASE.read_text(encoding="utf-8")

    assert 'id="plus-button"' in base
    assert 'id="image-button"' in base
    assert 'id="file-button"' in base
    assert "Open connected tools and attachments" in wrapper
    assert "Connected tools" in wrapper
    assert "['render','🟣','Render']" in wrapper
    assert "['github','⚫','GitHub']" in wrapper
    assert "['neon','🟢','Neon']" in wrapper
    assert "War Room" in wrapper
    assert "Credentials are never shown" in wrapper


def test_plus_connectors_reuse_founder_workbench_inspection_routes():
    wrapper = WRAPPER.read_text(encoding="utf-8")

    assert "workbenchUrl" in wrapper
    assert "mission_control.smi_workbench_status" in wrapper
    assert "item.inspect_url" in wrapper
    assert "Reading governed provider state" in wrapper
    assert "credentials:'same-origin'" in wrapper
    assert "inspectConnector" in wrapper


def test_plus_connector_surface_does_not_add_mutation_shortcuts():
    wrapper = WRAPPER.read_text(encoding="utf-8")

    assert "/mission/tools/render/deploy" not in wrapper
    assert "/mission/tools/github/write" not in wrapper
    assert "/mission/tools/neon/sql" not in wrapper
    assert "consequential actions still require Human Authority" in wrapper
    assert "toolsButton" not in wrapper
