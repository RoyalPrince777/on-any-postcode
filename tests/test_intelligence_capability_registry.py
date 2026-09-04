from oap.smi.intelligence_capability_registry import (
    COMMERCIAL_JOURNEY,
    LOCKED_WORLD_IDS,
    capabilities,
    capabilities_for_world,
    select_capabilities,
    status,
    validate_registry,
)


def test_registry_preserves_one_brain_seven_worlds_and_26_capabilities():
    validation = validate_registry(LOCKED_WORLD_IDS)
    assert validation["passed"] is True
    assert validation["world_count"] == 7
    assert validation["capability_count"] == 26
    assert validation["creates_intelligence_worlds"] is False
    assert validation["creates_agents"] is False
    assert validation["creates_brain"] is False
    assert validation["brain_count_added"] == 0
    assert validation["human_authority_final"] is True


def test_registry_capabilities_are_unique_and_only_reference_locked_worlds():
    items = capabilities()
    ids = [item.capability_id for item in items]
    names = [item.name for item in items]
    assert len(ids) == len(set(ids)) == 26
    assert len(names) == len(set(names)) == 26
    for item in items:
        assert item.world_ids
        assert set(item.world_ids) <= set(LOCKED_WORLD_IDS)


def test_every_locked_world_can_use_registry_capabilities():
    for world_id in LOCKED_WORLD_IDS:
        assert capabilities_for_world(world_id)


def test_commercial_journey_is_founder_approved_order():
    assert COMMERCIAL_JOURNEY == (
        "Explorer",
        "Discover",
        "Compare",
        "Plan",
        "Travel",
        "Stay",
        "Activity/Adventure",
        "Book",
        "Pay",
        "Pass",
        "Move",
        "Experience",
        "Support",
        "Chronicle",
    )


def test_transaction_and_supply_capabilities_fail_closed():
    current = status()
    assert current["registry_software_ready"] is True
    assert current["architecture_defined"] is True
    assert current["supply_integrations_connected"] is False
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
    assert current["transaction_execution_ready"] is False
    assert current["oap_travel_agency"]["production_claim_allowed"] is False
    assert current["oap_travel_agency"]["hidden_fees_allowed"] is False
    assert "booking" in current["transactional_capability_ids"]
    assert "payment" in current["transactional_capability_ids"]
    assert "agency" in current["transactional_capability_ids"]


def test_capability_selection_is_bounded_and_world_aware():
    selected = select_capabilities(
        "Compare hotel availability, price, booking and payment for my trip",
        world_ids=("earth", "movement", "civic", "matrix"),
    )
    assert "travel" in selected or "stay" in selected
    assert "availability" in selected
    assert "pricing" in selected
    assert "booking" in selected
    assert "payment" in selected
    assert "alignment" in selected
    assert len(selected) <= 8


def test_system_boundary_contract_stays_locked():
    current = status()
    assert current["creates_intelligence_worlds"] is False
    assert current["creates_agents"] is False
    assert current["creates_brain"] is False
    assert current["external_provider_authority"] is False
    assert current["human_authority_final"] is True
    assert current["validation"]["matrix_agents_remain_inside_matrix"] is True
    assert current["validation"]["nexus_connected"] is True
    assert current["validation"]["oasis_presentation_layer"] is True
    assert current["validation"]["guardian_gate_required"] is True
