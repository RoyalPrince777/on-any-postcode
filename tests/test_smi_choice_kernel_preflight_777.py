from mission_control.smi_choice_kernel_preflight_777 import preflight_choice

OPTIONS = [{"id": "existing-kernel", "evidence_verified": True}]

def test_preflight_is_never_execution():
    result = preflight_choice("SMI-777", "upgrade", OPTIONS, {
        "guardian_authorised": True, "founder_authorised": True,
        "evidence_verified": True,
    })
    assert result["ready"]
    assert result["advisory_gates_satisfied"] is True
    assert result["executed"] is False
    assert result["kernel_receipt_verified"] is False
    assert result["hrm_receipt_recorded"] is False
    assert result["votes_executed"] is False
    assert result["operational_vpi"] is None

def test_missing_approval_fails_advisory_gate():
    result = preflight_choice("SMI-777", "upgrade", OPTIONS)
    assert result["ready"]
    assert result["advisory_gates_satisfied"] is False
    assert result["executed"] is False

def test_invalid_mission_fails_closed():
    result = preflight_choice("", "upgrade", OPTIONS)
    assert result == {"ready": False, "reason": "mission_id_required", "executed": False}

def test_duplicate_options_fail_closed():
    result = preflight_choice("SMI-777", "upgrade", OPTIONS + OPTIONS)
    assert not result["ready"]
