from oap.smi import state_ownership_registry as registry


def test_registry_preserves_single_brain_and_unique_state_domains():
    status = registry.status()
    assert status["architecture_passed"] is True
    assert status["domain_count"] >= 10
    assert status["validation"]["unique_domains"] is True
    assert status["validation"]["creates_database"] is False
    assert status["validation"]["creates_brain"] is False
    assert status["validation"]["creates_intelligence_world"] is False
    assert status["fail_closed_on_conflict"] is True
    assert status["all_runtime_bindings_proven"] is False


def test_matching_owner_claims_are_coherent():
    result = registry.assess_claims((
        {"component": "arena-runtime", "state_ownership_claims": {"arena_competition": "arena", "identity": "identity"}},
    ))
    assert result["coherent"] is True
    assert result["human_review_required"] is False
    assert result["conflicts"] == ()


def test_owner_mismatch_fails_closed_for_human_review():
    result = registry.assess_claims((
        {"component": "market-runtime", "state_ownership_claims": {"value": "market"}},
    ))
    assert result["coherent"] is False
    assert result["human_review_required"] is True
    assert result["conflicts"][0]["reason"] == "owner_mismatch"
    assert result["conflicts"][0]["expected_owner"] == "sika"
    assert result["silent_resolution_performed"] is False


def test_unknown_domain_fails_closed():
    result = registry.assess_claims((
        {"component": "experimental-runtime", "state_ownership_claims": {"new_parallel_truth": "experimental"}},
    ))
    assert result["coherent"] is False
    assert result["conflicts"][0]["reason"] == "unknown_state_domain"
