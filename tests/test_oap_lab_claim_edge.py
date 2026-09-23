"""Negative proof of isolated OAP LAB Claim Edge contract."""
from dataclasses import replace
from hashlib import sha256
from uuid import UUID

import pytest

from mission_control.oap_lab_claim_edge import (
    ClaimEdge, ClaimEdgeBlocked, Source, admit_claim,
)
from mission_control.oap_lab_research import DOMAINS, MISSIONS, Notebook

OWNER = str(UUID(int=1))
OTHER = str(UUID(int=2))
MISSION = str(UUID(int=3))
CLAIM = str(UUID(int=4))
RAW = b"synthetic offline source: no real-world allegation"


def notebook(mission=MISSIONS[0], domain=DOMAINS[0]):
    return Notebook("lab-001", mission, domain, "Question?", "Hypothesis", "Falsification")


def edge(**changes):
    values = dict(
        claim_id=CLAIM, mission_id=MISSION, notebook_id="lab-001",
        domain=DOMAINS[0], claim="Synthetic research claim", subject="OAP LAB",
        relation="documents", object="Research", event_at="2026-01-01T00:00:00Z",
        owner_id=OWNER,
    )
    values.update(changes)
    return ClaimEdge(**values)


def source(**changes):
    values = dict(
        source_id="src-a", original=RAW,
        expected_sha256=sha256(RAW).hexdigest(),
        published_at="2026-01-01T00:00:00Z",
        retrieved_at="2026-01-02T00:00:00Z",
        independent_origin="original-a",
    )
    values.update(changes)
    return Source(**values)


@pytest.mark.parametrize("mission", MISSIONS)
def test_all_eight_lab_missions_use_one_contract(mission):
    result = admit_claim(edge(), notebook(mission), (source(),), authenticated_owner_id=OWNER)
    assert result["review_only"] is True
    assert result["scientific_truth_established"] is False


@pytest.mark.parametrize("domain", DOMAINS)
def test_all_twenty_one_domains_use_one_contract(domain):
    result = admit_claim(edge(domain=domain), notebook(domain=domain), (source(),),
                         authenticated_owner_id=OWNER)
    assert result["domain"] == domain


def test_verified_source_bytes_are_required():
    with pytest.raises(ClaimEdgeBlocked, match="source_byte_integrity_failed"):
        source(original=b"modified")
    with pytest.raises(ClaimEdgeBlocked, match="original_source_bytes_required"):
        source(original=b"")


@pytest.mark.parametrize("changes", [
    {"source_id": ""}, {"published_at": "not-a-date"},
    {"retrieved_at": "2025-01-01T00:00:00Z"},
    {"published_at": "2026-01-01"},
])
def test_invalid_source_rejected(changes):
    with pytest.raises(ClaimEdgeBlocked):
        source(**changes)


@pytest.mark.parametrize("changes", [
    {"relation": "secret_collusion"},
    {"domain": "nonexistent"},
    {"classification": "proven_by_founder"},
    {"owner_id": "not-an-id"},
    {"private_subject": True},
    {"private_subject": True, "consent_for_research": True},
    {"event_at": "2030-01-01T00:00:00Z"},
])
def test_invalid_claim_or_relationship_rejected(changes):
    if changes.get("event_at"):
        with pytest.raises(ClaimEdgeBlocked, match="future_event_at_retrieval"):
            admit_claim(edge(**changes), notebook(), (source(),), authenticated_owner_id=OWNER)
    else:
        with pytest.raises(ClaimEdgeBlocked):
            edge(**changes)


def test_wrong_owner_and_wrong_notebook_blocked():
    with pytest.raises(ClaimEdgeBlocked, match="owner_scope_mismatch"):
        admit_claim(edge(), notebook(), (source(),), authenticated_owner_id=OTHER)
    with pytest.raises(ClaimEdgeBlocked, match="lab_notebook_reference_mismatch"):
        admit_claim(edge(notebook_id="another"), notebook(), (source(),),
                    authenticated_owner_id=OWNER)


def test_stop_and_external_action_blocked():
    with pytest.raises(ClaimEdgeBlocked, match="stop_asserted"):
        admit_claim(edge(stopped=True), notebook(), (source(),), authenticated_owner_id=OWNER)
    with pytest.raises(ClaimEdgeBlocked, match="consequential_execution_forbidden"):
        admit_claim(edge(), notebook(), (source(),), authenticated_owner_id=OWNER,
                    external_action=True)


def test_fake_established_status_rejected_even_with_two_claimed_origins():
    with pytest.raises(ClaimEdgeBlocked, match="independent_review_required"):
        admit_claim(edge(classification="established"), notebook(),
                    (source(), source(source_id="src-b", independent_origin="original-b")),
                    authenticated_owner_id=OWNER)


def test_claimed_independence_is_not_verified_independence():
    result = admit_claim(edge(), notebook(),
                         (source(), source(source_id="src-b", independent_origin="original-b")),
                         authenticated_owner_id=OWNER)
    assert result["independent_origins_claimed"] == 2
    assert result["independence_verified"] is False
    assert result["canonical_promotion_authorised"] is False
    assert result["publication_authorised"] is False
    assert result["execution_authorised"] is False


def test_duplicate_source_id_and_missing_sources_rejected():
    with pytest.raises(ClaimEdgeBlocked, match="duplicate_source_id"):
        admit_claim(edge(), notebook(), (source(), source()), authenticated_owner_id=OWNER)
    with pytest.raises(ClaimEdgeBlocked, match="verified_source_required"):
        admit_claim(edge(), notebook(), (), authenticated_owner_id=OWNER)


def test_reproducible_secret_safe_receipt():
    a = admit_claim(edge(private_subject=True, consent_for_research=True, redacted=True),
                    notebook(), (source(),), authenticated_owner_id=OWNER)
    b = admit_claim(edge(private_subject=True, consent_for_research=True, redacted=True),
                    notebook(), (source(),), authenticated_owner_id=OWNER)
    assert a == b
    assert a["private_subject_redacted"] is True
    assert a["receipt_sha256"] != a["source_sha256"][0]
    assert RAW.decode() not in str(a)
    assert "Synthetic research claim" not in str(a)
