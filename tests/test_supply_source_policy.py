from oap.smi import supply_source_policy, travel_agency


def test_supply_policy_keeps_booking_com_optional():
    current = supply_source_policy.status()

    assert current["policy_ready"] is True
    assert current["oap_direct_preferred_when_comparable"] is True
    assert current["external_suppliers_allowed"] is True
    assert current["external_suppliers_optional"] is True
    assert current["single_external_provider_dependency_allowed"] is False
    assert current["booking_com_required"] is False
    assert current["external_provider_authority"] is False
    assert current["creates_intelligence_worlds"] is False
    assert current["creates_agents"] is False
    assert current["creates_brain"] is False
    assert current["human_authority_final"] is True


def test_comparable_direct_supply_wins_only_source_tiebreak():
    ranked = supply_source_policy.rank_comparable_sources(
        (
            {
                "source_id": "booking_com",
                "source_kind": "external",
                "title": "External Stay",
            },
            {
                "source_id": "oap_direct",
                "source_kind": "oap_direct",
                "title": "Direct Stay",
            },
        )
    )

    assert ranked[0]["source_id"] == "oap_direct"
    assert ranked[0]["source_priority"] == 0
    assert ranked[1]["source_id"] == "booking_com"
    assert ranked[1]["source_priority"] == 100


def test_travel_agency_exposes_supplier_independence_policy():
    current = travel_agency.status()

    assert current["supplier_independence_policy_ready"] is True
    assert current["oap_direct_preferred_when_comparable"] is True
    assert current["external_suppliers_optional"] is True
    assert current["single_external_provider_dependency_allowed"] is False
    assert current["booking_com_required"] is False
    assert current["preferred_supply_source_order"] == (
        "oap_direct",
        "replaceable_external_supply",
    )

    gate_states = {gate["id"]: gate["ready"] for gate in current["gates"]}
    assert gate_states["supplier_independence_policy"] is True
