from __future__ import annotations

from pathlib import Path


TEMPLATE = Path("mission_control/templates/smi_a7.html")
VIEWS = Path("mission_control/smi_proof_views.py")


def test_a7_dashboard_exposes_real_founder_proof_path_without_fake_enable_control():
    page = TEMPLATE.read_text(encoding="utf-8")

    assert "Close the current Green Gate" in page
    assert "mission_control.ollama_chat_dashboard" in page
    assert "mission_control.judgement_dashboard" in page
    assert "my_world_workspace" in page
    assert "hrm-memory" in page
    assert "smi_proof_gate.rollback_recovery_proof" in page
    assert "Run Rollback / Recovery Proof" in page
    assert "Approval signing key" in page
    assert "A7 is not enabled here" in page
    assert "Enable A7" not in page


def test_a7_dashboard_reads_green_gate_and_approval_readiness():
    views = VIEWS.read_text(encoding="utf-8")

    assert "green_gate=smi_proof_gate.public_safe_status()" in views
    assert "approval=approval_service.status()" in views
    assert "founder_only=True" in views
