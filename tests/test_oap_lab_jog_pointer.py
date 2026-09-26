"""Privacy and negative coverage for existing-Organiser LAB research pointer."""
from uuid import UUID

import pytest

from mission_control.oap_lab_claim_edge import ClaimEdgeBlocked
from mission_control.oap_lab_jog_pointer import research_jog_pointer

OWNER = str(UUID(int=1))
OTHER = str(UUID(int=2))
MISSION = str(UUID(int=3))
CLAIM = str(UUID(int=4))


def handoff():
    return {
        "claim_id": CLAIM,
        "mission_id": MISSION,
        "notebook_id": "lab-001",
        "claim_receipt_sha256": "a" * 64,
        "review_receipt_sha256": "b" * 64,
        "handoff": "read_only_research_review",
        "jog_memory_pointer_only": True,
        "durable_storage_verified": False,
        "independent_origin_verified": False,
        "scientific_truth_established": False,
        "canonical_promotion_authorised": False,
        "publication_authorised": False,
        "execution_authorised": False,
        "raw_secret": "must never enter memory",
        "claim_text": "must never enter memory",
    }


def project(**changes):
    values = {
        "authenticated_owner_id": OWNER,
        "stored_owner_id": OWNER,
        "stored_mission_id": MISSION,
        "stored_notebook_id": "lab-001",
    }
    values.update(changes)
    return research_jog_pointer(handoff(), **values)


def test_owner_scoped_reference_excludes_claims_and_raw_sources():
    value = project()
    assert value["graph_mode"] == "reference_only_no_graph_write"
    assert value["organiser_mode"] == "read_only_resume_pointer"
    assert value["hrm_mode"] == "no_authority_receipt"
    assert value["execution_authorised"] is False
    assert value["scientific_truth_established"] is False
    assert "must never enter memory" not in str(value)
    assert "raw_secret" not in value
    assert "claim_text" not in value


@pytest.mark.parametrize("changes", [
    {"authenticated_owner_id": OTHER},
    {"stored_owner_id": OTHER},
    {"stored_mission_id": str(UUID(int=99))},
    {"stored_notebook_id": "wrong"},
    {"stopped": True},
])
def test_wrong_scope_and_stop_fail_closed(changes):
    with pytest.raises(ClaimEdgeBlocked):
        project(**changes)


@pytest.mark.parametrize("key,value", [
    ("claim_id", "not-a-uuid"),
    ("mission_id", str(UUID(int=99))),
    ("notebook_id", "wrong"),
    ("claim_receipt_sha256", "not-a-hash"),
    ("review_receipt_sha256", ""),
    ("handoff", "approved_for_release"),
    ("jog_memory_pointer_only", False),
    ("durable_storage_verified", True),
    ("independent_origin_verified", True),
    ("scientific_truth_established", True),
    ("canonical_promotion_authorised", True),
    ("publication_authorised", True),
    ("execution_authorised", True),
])
def test_invalid_or_escalated_handoff_rejected(key, value):
    altered = {**handoff(), key: value}
    with pytest.raises(ClaimEdgeBlocked):
        research_jog_pointer(
            altered, authenticated_owner_id=OWNER, stored_owner_id=OWNER,
            stored_mission_id=MISSION, stored_notebook_id="lab-001",
        )


def test_missing_handoff_rejected():
    with pytest.raises(ClaimEdgeBlocked):
        research_jog_pointer(
            None, authenticated_owner_id=OWNER, stored_owner_id=OWNER,
            stored_mission_id=MISSION, stored_notebook_id="lab-001",
        )
