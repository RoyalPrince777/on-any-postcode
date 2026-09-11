from pathlib import Path

WRAPPER = Path("mission_control/templates/ollama_chat.html")


def test_personal_smi_chat_ui_final_gate_contract():
    text = WRAPPER.read_text(encoding="utf-8")
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
    text = WRAPPER.read_text(encoding="utf-8")
    assert "private chain-of-thought stays private" in text
    assert "Nothing runs before approval" in text
    assert "Credentials never appear here" in text
    assert "signed receipt" in text
    assert "can_execute===false" in text
