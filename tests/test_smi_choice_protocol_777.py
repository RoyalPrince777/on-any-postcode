from mission_control.smi_choice_protocol_777 import compare_choices, execution_gate

def test_choice_comparison_does_not_execute_or_invent_votes():
    result = compare_choices("M-777", "upgrade", [{"id": "A", "evidence_verified": True},
                                                   {"id": "B"}])
    assert result["ready"]
    assert result["comparison"][0]["evidence_status"] == "verified"
    assert result["comparison"][1]["evidence_status"] == "unverified"
    assert result["agent_votes_executed"] is False
    assert result["execution_authorised"] is False
    assert result["operational_vpi"] is None

def test_invalid_inputs_fail_closed():
    assert not compare_choices("", "vote", [{"id": "A"}])["ready"]
    assert not compare_choices("M", "unknown", [{"id": "A"}])["ready"]
    assert not compare_choices("M", "vote", [{"id": "A"}, {"id": "A"}])["ready"]
    assert not compare_choices("M", "vote", [])["ready"]

def test_execution_requires_all_explicit_gates():
    assert not execution_gate({})
    assert not execution_gate({"guardian_authorised": True, "founder_authorised": True})
    assert execution_gate({"guardian_authorised": True, "founder_authorised": True,
                           "evidence_verified": True})
