from pathlib import Path

WRAPPER = Path("mission_control/templates/ollama_chat.html")
JS = Path("mission_control/static/smi_chat_final.js")
CSS = Path("mission_control/static/smi_chat_final.css")


def _surface_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in (WRAPPER, JS, CSS)
    )


def test_personal_smi_chat_ui_final_gate_contract():
    text = _surface_text()
    required = (
        "Personal SMI",
        "Search conversations",
        "Retry",
        "Edit",
        "Governed GitHub Action",
        "Prepare exact plan",
        "Execute through Living Kernel",
        "JOOG / HRM receipt",
        "oap-smi-complete",
        "Truth gate green",
        "drop-active",
        "founder_tools.github_action_approval",
        "founder_tools.github_execute_approved_action",
        "mission_control.smi_workbench_status",
        "mission_control.smi_chat_health",
    )
    for marker in required:
        assert marker in text


def test_personal_smi_chat_ui_keeps_truth_boundaries():
    text = _surface_text()
    assert "private chain-of-thought stays private" in text
    assert "Nothing runs before approval" in text
    assert "Credentials never appear here" in text
    assert "signed receipt" in text
    assert "can_execute===false" in text


def test_personal_smi_final_controller_is_scope_isolated():
    text = JS.read_text(encoding="utf-8")
    assert text.startswith("(()=>{")
    assert text.rstrip().endswith("})();")
    assert "const plusButton=" not in text
    assert "const attachMenu=" not in text
