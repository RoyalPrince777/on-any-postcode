from mission_control.silicon_reference_platform import (
    ACCEPTANCE_GATES,
    HARDWARE_CAPABILITY_CLASSES,
    PHYSICAL_DEVICE_BUILT,
    PLATFORM_STATUS,
    PURCHASE_REQUIRED_BY_SPEC,
    REFERENCE_GENERATION,
    VENDOR_LOCK_IN_ALLOWED,
    assess_candidate,
    reference_platform_contract,
    validate_reference_platform_contract,
)


def test_reference_platform_contract_is_valid_and_vendor_neutral():
    validate_reference_platform_contract()
    contract = reference_platform_contract()

    assert REFERENCE_GENERATION == 1
    assert PLATFORM_STATUS == "SPECIFICATION_READY"
    assert PHYSICAL_DEVICE_BUILT is False
    assert PURCHASE_REQUIRED_BY_SPEC is False
    assert VENDOR_LOCK_IN_ALLOWED is False
    assert contract["human_authority_final"] is True
    assert len(HARDWARE_CAPABILITY_CLASSES) == 7
    assert len(ACCEPTANCE_GATES) == 7


def test_all_acceptance_evidence_is_required():
    full_evidence = {gate["proof"]: True for gate in ACCEPTANCE_GATES}
    ready = assess_candidate(full_evidence)

    assert ready["candidate_ready"] is True
    assert ready["passed_count"] == 7
    assert ready["activation_performed"] is False

    missing_one = dict(full_evidence)
    missing_one[ACCEPTANCE_GATES[0]["proof"]] = False
    blocked = assess_candidate(missing_one)

    assert blocked["candidate_ready"] is False
    assert blocked["passed_count"] == 6
    assert blocked["activation_performed"] is False


def test_unknown_or_truthy_values_do_not_count_as_proof():
    evidence = {gate["proof"]: True for gate in ACCEPTANCE_GATES}
    evidence[ACCEPTANCE_GATES[-1]["proof"]] = "yes"

    result = assess_candidate(evidence)

    assert result["candidate_ready"] is False
    assert result["human_authority_final"] is True


def test_optional_acceleration_never_becomes_a_hard_requirement():
    acceleration = next(
        item for item in HARDWARE_CAPABILITY_CLASSES if item["id"] == "acceleration"
    )

    assert acceleration["required"] is False
    assert "software_fallback_required" in acceleration["requirements"]
