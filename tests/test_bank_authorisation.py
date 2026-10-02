from mission_control import bank_authorisation


def test_bank_authorisation_register_has_concrete_evidence_categories():
    register = bank_authorisation.evidence_register()

    assert len(register) == 30
    assert "capital_source_and_proof" in register
    assert "icaap" in register
    assert "ilaap" in register
    assert "aml_ctf_framework" in register
    assert "sanctions_screening_and_ofsi_process" in register
    assert "mobilisation_plan" in register
    assert "authorisation_decision_evidence" in register
    assert all(item["proven"] is False for item in register.values())


def test_bank_status_never_uses_humanitarian_purpose_as_licence_bypass():
    status = bank_authorisation.readiness_status()

    assert status["route"] == "PRA/FCA new-bank authorisation"
    assert status["authorised_bank"] is False
    assert status["deposit_taking_enabled"] is False
    assert status["regulated_execution_enabled"] is False
    assert status["permission_scope_required"] is True
    assert status["humanitarian_or_human_rights_purpose_bypasses_authorisation"] is False


def test_regulated_bank_capabilities_require_authorisation_and_production_proof():
    for capability in bank_authorisation.REGULATED_CAPABILITIES:
        assert bank_authorisation.capability_allowed(capability) is False
        assert (
            bank_authorisation.capability_allowed(
                capability,
                regulator_authorisation_proven=True,
                production_gate_passed=False,
                permission_scope_allows=True,
            )
            is False
        )
        assert (
            bank_authorisation.capability_allowed(
                capability,
                regulator_authorisation_proven=True,
                production_gate_passed=True,
                permission_scope_allows=True,
            )
            is True
        )


def test_unknown_capability_never_opens():
    assert (
        bank_authorisation.capability_allowed(
            "invented_capability",
            regulator_authorisation_proven=True,
            production_gate_passed=True,
        )
        is False
    )
