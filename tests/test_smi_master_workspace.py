from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Rebased on the governed Studio 21 generation backend.
BASE = ROOT / "mission_control" / "templates" / "ollama_chat_base.html"
FINAL = ROOT / "mission_control" / "static" / "smi_chat_final.js"
CANONICAL = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"


def test_master_tools_plus_is_reachable_and_scrollable():
    base = BASE.read_text(encoding="utf-8")
    assert 'id="plus-button"' in base
    assert 'aria-label="Open Master Tools and attachments"' in base
    assert 'aria-label="Master Tools"' in base
    assert "max-height:min(70dvh,620px)" in base
    assert "overflow-y:auto" in base
    assert "z-index:80" in base


def test_master_tools_remain_openable_while_response_runs():
    base = BASE.read_text(encoding="utf-8")
    assert "plusButton.disabled=false" in base
    assert "imageButton.disabled=running" in base
    assert "fileButton.disabled=running" in base


def test_saved_work_has_refresh_count_search_and_current_selection():
    base = BASE.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")
    for marker in (
        "Saved Work",
        'id="history-count"',
        'id="refresh-history"',
        "Saved automatically · select work to continue",
        "row.dataset.conversationId=item.conversation_id",
        "row.classList.add('active')",
        "Saved work restored · continue from here · Human Authority final",
    ):
        assert marker in base
    assert "Search conversations" in final
    assert "☰ Saved" in final


def test_visible_master_tool_buttons_have_real_handlers():
    base = BASE.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")
    for connector in ("render", "github", "neon"):
        assert f'data-connector-id="{connector}"' in base
    for action in (
        "war-room","function-health","green-gate","hrm",
        "improvement","swot","behaviour","github-governed",
    ):
        assert f'data-oap-action="{action}"' in base
    assert "qa('[data-connector-id]').forEach" in final
    assert "qa('[data-oap-action]').forEach" in final
    assert "fetch(item.inspect_url" in final
    assert "githubAction()" in final


def test_studio_button_reads_governed_21_backend_truth():
    final = FINAL.read_text(encoding="utf-8")
    assert "generation_backend_configured" in final
    assert "full_live_certificate" in final
    assert "generation_tools" in final
    assert "SMI 21 governed generation" in final


def test_core_chat_controls_have_single_canonical_owners():
    canonical = CANONICAL.read_text(encoding="utf-8")
    for marker in (
        "singleSubmitOwner:true","composerOwner:true","plusOwner:true",
        "pauseOwner:true","micOwner:true","voiceOwner:true","stopOwner:true",
        "cameraCapture:true","screenCapture:true",
    ):
        assert marker in canonical


def test_master_workspace_contract_is_explicit():
    final = FINAL.read_text(encoding="utf-8")
    assert "window.OAP_SMI_MASTER={version:'1.2',masterTools:true,savedWork:true,search:true,studio21:true,studioExecution:true,buttonProof:true,autoDepthVisible:true,governedActions:true}" in final


def test_studio_creation_tools_execute_from_master_tools():
    base = BASE.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")
    for tool in ("imagine", "bring_alive", "scene_builder"):
        assert f'data-studio-tool="{tool}"' in base
    for marker in (
        "studioGenerateUrl",
        "studioVideoStatusUrlTemplate",
        "studioVideoContentUrlTemplate",
        "runStudioTool",
        "pollStudioVideo",
        "artifact_proven",
        "X-OAP-CSRF",
    ):
        assert marker in final or marker in (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text(encoding="utf-8")


def test_button_proof_is_a_first_class_master_tool():
    base = BASE.read_text(encoding="utf-8")
    wrapper = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")
    assert 'data-oap-action="button-proof"' in base
    assert "buttonProofUrl" in wrapper
    assert "Button Proof" in final
