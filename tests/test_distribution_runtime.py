from __future__ import annotations

import pytest

from mission_control import distribution_runtime


def test_distribution_runtime_state_machine_covers_operational_loop():
    assert distribution_runtime.STATES[:10] == (
        "CREATED",
        "RIGHTS_READY",
        "LISTED",
        "ORDERED",
        "DISTRIBUTION_READY",
        "ROUTED",
        "HANDED_OFF",
        "DELIVERED",
        "RECEIPT_RECORDED",
        "CLOSED",
    )
    assert {
        "STOPPED",
        "DISPUTED",
        "RETURNED",
        "FAILED",
        "RECOVERY_REQUIRED",
    }.issubset(distribution_runtime.STATES)


@pytest.mark.parametrize(
    ("current", "target"),
    (
        ("CREATED", "RIGHTS_READY"),
        ("RIGHTS_READY", "LISTED"),
        ("LISTED", "ORDERED"),
        ("ORDERED", "DISTRIBUTION_READY"),
        ("DISTRIBUTION_READY", "ROUTED"),
        ("ROUTED", "HANDED_OFF"),
        ("ROUTED", "DELIVERED"),
        ("HANDED_OFF", "DELIVERED"),
        ("DELIVERED", "RECEIPT_RECORDED"),
        ("RECEIPT_RECORDED", "CLOSED"),
        ("DELIVERED", "RECOVERY_REQUIRED"),
        ("RECOVERY_REQUIRED", "DELIVERED"),
    ),
)
def test_valid_distribution_transitions(current: str, target: str):
    assert distribution_runtime.validate_transition(current, target) == (
        current,
        target,
    )


@pytest.mark.parametrize(
    ("current", "target"),
    (
        ("CREATED", "DELIVERED"),
        ("ORDERED", "CLOSED"),
        ("CLOSED", "ROUTED"),
        ("STOPPED", "RIGHTS_READY"),
        ("RETURNED", "DELIVERED"),
        ("FAILED", "CLOSED"),
    ),
)
def test_invalid_distribution_transitions_fail_closed(current: str, target: str):
    with pytest.raises(
        distribution_runtime.DistributionRuntimeError,
        match="distribution_transition_not_allowed",
    ):
        distribution_runtime.validate_transition(current, target)


def _event(
    *,
    distribution_id: str,
    owner_identity_id: str,
    from_state: str | None,
    to_state: str,
    evidence_reference: str,
    previous_hash: str,
):
    event_hash = distribution_runtime._event_hash(
        distribution_id=distribution_id,
        owner_identity_id=owner_identity_id,
        from_state=from_state,
        to_state=to_state,
        evidence_reference=evidence_reference,
        previous_hash=previous_hash,
    )
    return {
        "distribution_id": distribution_id,
        "owner_identity_id": owner_identity_id,
        "from_state": from_state,
        "to_state": to_state,
        "evidence_reference": evidence_reference,
        "previous_hash": previous_hash,
        "event_hash": event_hash,
    }


def test_event_receipt_chain_detects_tampering():
    distribution_id = "11111111-1111-1111-1111-111111111111"
    owner_id = "22222222-2222-2222-2222-222222222222"
    first = _event(
        distribution_id=distribution_id,
        owner_identity_id=owner_id,
        from_state=None,
        to_state="CREATED",
        evidence_reference="source:1",
        previous_hash="",
    )
    second = _event(
        distribution_id=distribution_id,
        owner_identity_id=owner_id,
        from_state="CREATED",
        to_state="RIGHTS_READY",
        evidence_reference="rights:1",
        previous_hash=first["event_hash"],
    )
    verified = distribution_runtime.verify_event_chain([first, second])
    assert verified["verified"] is True
    assert verified["event_count"] == 2
    assert verified["head_hash"] == second["event_hash"]

    second["evidence_reference"] = "tampered"
    broken = distribution_runtime.verify_event_chain([first, second])
    assert broken["verified"] is False
    assert broken["reason"] == "event_hash_mismatch"


def test_schema_has_runtime_event_ledger_owner_scope_and_order_link():
    sql = "\n".join(distribution_runtime.SCHEMA_STATEMENTS)

    assert "oap_distribution_runtime" in sql
    assert "oap_distribution_runtime_events" in sql
    assert "owner_identity_id UUID NOT NULL REFERENCES users(id)" in sql
    assert "order_id UUID NULL REFERENCES oap_commerce_orders(order_id)" in sql
    assert "event_hash TEXT NOT NULL UNIQUE" in sql
    assert "UNIQUE(owner_identity_id,lane,subject_type,subject_id)" in sql


def test_runtime_status_preserves_non_live_truth_boundary():
    status = distribution_runtime.status()

    assert len(status["lanes"]) == 7
    assert status["append_only_event_chain"] is True
    assert status["owner_scoped_tracking"] is True
    assert status["analytics_available"] is True
    assert status["recovery_state_supported"] is True
    assert status["external_execution_enabled"] is False
    assert status["payment_capture"] is False
    assert status["dispatch_execution"] is False
    assert status["carrier_handoff_execution"] is False
    assert status["human_authority_final"] is True


def test_runtime_schema_initialization_requires_explicit_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        distribution_runtime.init_schema()

    dry = distribution_runtime.init_schema(assume_yes=True)
    assert dry["dry_run"] is True
    assert dry["migration"] == distribution_runtime.MIGRATION_VERSION
    assert dry["statements"] == 4


def test_distribution_runtime_routes_are_registered(app):
    rules = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/mission/organs/distribution/runtime" in rules
    assert "/mission/organs/distribution/runtime/<distribution_id>" in rules
    assert "/mission/organs/distribution/runtime/<distribution_id>/transition" in rules
