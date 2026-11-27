from mission_control import master_upgrade_contract as contract


def test_private_origin_only_exact_wsgi_port():
    assert contract.private_origin_allowed("5000") is True
    for value in ("5052", "443", "5000 ", "", None, 5000):
        assert contract.private_origin_allowed(value) is False


def test_master_release_law_does_not_grant_or_claim_runtime_authority():
    result = contract.status()
    rules = result["rules"]
    assert rules["private_origin_required"] is True
    assert rules["automatic_publication"] is False
    assert rules["simulation_counts_as_runtime_proof"] is False
    assert rules["code_or_ci_counts_as_runtime_proof"] is False
    assert rules["ecosystem_wide_runtime_enforcement_verified"] is False
    assert "founder_final" in rules["release_evidence_requirements"]
    assert result["overall_green"] is False
    assert result["locks"]["self_approval_enabled"] is False
