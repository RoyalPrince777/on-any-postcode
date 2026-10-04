from mission_control import infrastructure, telecom_sovereignty


def test_telecom_sovereignty_routes_are_one_stack_in_order():
    status = telecom_sovereignty.status()

    assert status["single_stack"] is True
    assert status["path"] == "A -> B -> C"
    assert [route["id"] for route in status["routes"]] == ["A", "B", "C"]
    assert status["validation"]["passed"] is True


def test_route_a_owns_identity_and_orchestration():
    route = telecom_sovereignty.ROUTES[0]

    assert route["id"] == "A"
    assert route["external_trust_required"] is False
    assert {"my_card", "oap_number", "network_passport", "guardian_policy"} <= set(
        route["components"]
    )


def test_route_b_is_profile_issuance_candidate_not_production_claim():
    route = telecom_sovereignty.ROUTES[1]
    status = telecom_sovereignty.status()

    assert route["id"] == "B"
    assert "smdp_plus_candidate" in route["components"]
    assert status["execution"]["production_profile_issuance_enabled"] is False
    assert status["execution"]["production_smdp_plus_claimed"] is False
    assert status["execution"]["external_certification_claimed"] is False


def test_route_c_keeps_radio_and_public_numbering_fail_closed():
    route = telecom_sovereignty.ROUTES[2]
    status = telecom_sovereignty.status()

    assert route["id"] == "C"
    assert {"private_mobile_core", "network_authentication", "radio_zone_registry"} <= set(
        route["components"]
    )
    assert status["execution"]["radio_transmission_enabled"] is False
    assert status["execution"]["public_number_issuance_enabled"] is False
    assert status["execution"]["carrier_activation_enabled"] is False


def test_external_trust_gates_are_explicit():
    gates = set(telecom_sovereignty.EXTERNAL_GATES)

    assert "gsma_compliance_and_production_pki" in gates
    assert "sas_sm_accreditation" in gates
    assert "certified_euicc_interoperability" in gates
    assert "lawful_spectrum_authority" in gates
    assert "public_numbering_authority" in gates


def test_human_authority_remains_final():
    assert telecom_sovereignty.EXECUTION_BOUNDARY["human_authority_required"] is True


def test_infrastructure_is_single_owner_of_telecom_sovereignty():
    projection = infrastructure.get_public_infrastructure()

    telecom = projection["telecom_sovereignty"]
    assert telecom["system"] == "OAP Telecom Sovereignty"
    assert telecom["single_stack"] is True
    assert telecom["validation"]["passed"] is True
