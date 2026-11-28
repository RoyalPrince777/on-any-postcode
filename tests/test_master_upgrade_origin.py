from datetime import UTC, datetime, timedelta

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


def test_release_hrm_review_is_digest_bound_and_never_authorizes(monkeypatch):
    from mission_control import hrm_durable_receipt

    digest = "a" * 64
    requested = []
    receipt = {"found": True, "read_back_verified": True,
               "authority_transferred": False,
               "recorded_at": datetime.now(UTC).isoformat()}

    def read(signal):
        requested.append(signal)
        return receipt if signal.endswith(digest) else {"found": False}

    monkeypatch.setattr(hrm_durable_receipt, "latest_receipt_status", read)
    result = contract.release_hrm_review("tda-london", digest)
    assert requested == ["release:tda-london:" + digest]
    assert result["fresh"] is True
    assert result["publication_authorized"] is False
    assert not contract.release_hrm_review("tda-london", "b" * 64)["receipt_found"]
    assert contract.release_hrm_review("tda-london", "bad")["reason"] == "invalid_candidate_digest"
    for delta in (timedelta(days=-2), timedelta(days=1)):
        receipt["recorded_at"] = (datetime.now(UTC) + delta).isoformat()
        assert not contract.release_hrm_review("tda-london", digest)["fresh"]
    receipt["recorded_at"] = "not-a-date"
    assert not contract.release_hrm_review("tda-london", digest)["fresh"]
    receipt["read_back_verified"] = False
    assert not contract.release_hrm_review("tda-london", digest)["readback_verified"]
