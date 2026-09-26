from __future__ import annotations

from pathlib import Path

TEMPLATE = Path("mission_control/templates/smi_a7.html")
VIEWS = Path("mission_control/smi_proof_views.py")
WEB_SECURITY = Path("mission_control/web_security.py")


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



def test_a7_dashboard_exposes_internal_live_proof_chain_only():
    page = TEMPLATE.read_text(encoding="utf-8")
    views = VIEWS.read_text(encoding="utf-8")

    assert "Run Public / Private Boundary Proof" in page
    assert "Run Constitutional Review" in page
    assert "Run Internal A7 Proof Chain" in page
    assert "smi_proof_gate.a7_public_private_boundary_proof" in page
    assert "smi_proof_gate.a7_constitutional_review_proof" in page
    assert '<option value="a7_public_private_boundary">' not in page
    assert '<option value="a7_constitutional_review">' not in page
    assert '@bp.post("/a7/public-private-boundary")' in views
    assert '@bp.post("/a7/constitutional-review")' in views
    assert "run_public_private_boundary_proof" in views
    assert "run_constitutional_review_proof" in views


def test_login_required_exposes_machine_readable_founder_policy_metadata():
    security = WEB_SECURITY.read_text(encoding="utf-8")
    assert "wrapped._oap_login_required = True" in security
    assert "wrapped._oap_founder_only = bool(founder_only)" in security
    assert 'wrapped._oap_auth_policy = "login-required-v1"' in security
