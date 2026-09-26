from mission_control import smi_capabilities


def test_smi_capability_status_exposes_state_ownership_truth():
    status = smi_capabilities.smi_capability_status()
    ownership = status["canonical_state_ownership"]
    assert ownership["architecture_passed"] is True
    assert ownership["fail_closed_on_conflict"] is True
    assert ownership["all_runtime_bindings_proven"] is False
    assert ownership["human_authority_final"] is True
