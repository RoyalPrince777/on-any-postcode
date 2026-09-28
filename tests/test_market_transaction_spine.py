from __future__ import annotations

import pytest

from mission_control import market_transaction_spine as spine


def test_schema_is_correlation_only_and_reuses_existing_organs():
    sql = "\n".join(spine.MARKET_TRANSACTION_SCHEMA_STATEMENTS)

    assert "oap_market_transactions" in sql
    assert "oap_market_transaction_events" in sql
    assert "REFERENCES oap_commerce_orders(order_id)" in sql
    assert "REFERENCES oap_commerce_fulfilment_intents(fulfilment_id)" in sql
    assert "REFERENCES oap_movement_bookings(booking_id)" in sql
    assert "REFERENCES oap_post_office_parcels(parcel_id)" in sql
    assert "REFERENCES oap_commerce_payment_intents(intent_id)" in sql
    assert "UNIQUE(buyer_identity_id,idempotency_key)" in sql


def test_schema_does_not_duplicate_authoritative_organs():
    sql = "\n".join(spine.MARKET_TRANSACTION_SCHEMA_STATEMENTS)

    assert "CREATE TABLE IF NOT EXISTS oap_commerce_orders" not in sql
    assert "CREATE TABLE IF NOT EXISTS oap_movement_bookings" not in sql
    assert "CREATE TABLE IF NOT EXISTS oap_post_office_parcels" not in sql


def test_truth_boundaries_do_not_add_external_execution_methods():
    forbidden = {
        "capture_payment",
        "transfer_money",
        "handoff_to_carrier",
        "dispatch_worker",
        "external_fulfilment",
    }
    assert forbidden.isdisjoint(dir(spine.MarketTransactionStore))


@pytest.mark.parametrize(
    ("kwargs", "state", "recovery", "last_good", "reason"),
    [
        (
            {
                "order_present": False,
                "fulfilment_expected": False,
                "fulfilment_present": False,
                "movement_expected": False,
                "movement_present": False,
                "parcel_expected": False,
                "parcel_present": False,
            },
            "RECOVERY_REQUIRED",
            "REQUIRED",
            "OPEN",
            "order_missing",
        ),
        (
            {
                "order_present": True,
                "fulfilment_expected": True,
                "fulfilment_present": False,
                "movement_expected": False,
                "movement_present": False,
                "parcel_expected": False,
                "parcel_present": False,
            },
            "RECOVERY_REQUIRED",
            "REQUIRED",
            "ORDER_RECORDED",
            "fulfilment_intent_missing",
        ),
        (
            {
                "order_present": True,
                "fulfilment_expected": True,
                "fulfilment_present": True,
                "movement_expected": True,
                "movement_present": False,
                "parcel_expected": False,
                "parcel_present": False,
            },
            "RECOVERY_REQUIRED",
            "REQUIRED",
            "FULFILMENT_PENDING",
            "movement_booking_missing",
        ),
        (
            {
                "order_present": True,
                "fulfilment_expected": True,
                "fulfilment_present": True,
                "movement_expected": True,
                "movement_present": True,
                "parcel_expected": True,
                "parcel_present": False,
            },
            "RECOVERY_REQUIRED",
            "REQUIRED",
            "MOVEMENT_PENDING",
            "parcel_missing",
        ),
    ],
)
def test_missing_expected_reference_requires_recovery(
    kwargs, state, recovery, last_good, reason
):
    result = spine.derive_recovery_state(**kwargs)

    assert result == {
        "state": state,
        "recovery_state": recovery,
        "last_good_stage": last_good,
        "reason": reason,
    }


def test_stop_wins_over_progress_and_blocks_consequential_action():
    result = spine.derive_recovery_state(
        order_present=True,
        fulfilment_expected=True,
        fulfilment_present=True,
        movement_expected=True,
        movement_present=True,
        parcel_expected=True,
        parcel_present=True,
        stopped=True,
    )

    assert result["state"] == "STOPPED"
    assert result["reason"] == "stop_active"
    assert (
        spine.consequential_action_allowed(
            stop_state="STOPPED", recovery_state="NONE"
        )
        is False
    )


@pytest.mark.parametrize(
    ("stop_state", "recovery_state"),
    [
        ("REQUESTED", "NONE"),
        ("STOPPED", "NONE"),
        ("RECOVERY_REQUIRED", "NONE"),
        ("NONE", "REQUIRED"),
        ("NONE", "IN_PROGRESS"),
        ("NONE", "FAILED"),
        ("UNKNOWN", "NONE"),
        ("NONE", "UNKNOWN"),
    ],
)
def test_consequential_action_fails_closed(stop_state, recovery_state):
    assert (
        spine.consequential_action_allowed(
            stop_state=stop_state, recovery_state=recovery_state
        )
        is False
    )


def test_consequential_action_can_resume_only_from_clear_state():
    assert spine.consequential_action_allowed(
        stop_state="NONE", recovery_state="NONE"
    )
    assert spine.consequential_action_allowed(
        stop_state="CLEARED_BY_HUMAN", recovery_state="RECOVERED"
    )


def test_recovery_preserves_last_good_stage_instead_of_fake_completion():
    result = spine.derive_recovery_state(
        order_present=True,
        fulfilment_expected=True,
        fulfilment_present=True,
        movement_expected=True,
        movement_present=True,
        parcel_expected=True,
        parcel_present=False,
    )

    assert result["state"] != "COMPLETED"
    assert result["last_good_stage"] == "MOVEMENT_PENDING"


def test_ready_reference_state_does_not_claim_payment_or_delivery_completion():
    result = spine.derive_recovery_state(
        order_present=True,
        fulfilment_expected=True,
        fulfilment_present=True,
        movement_expected=True,
        movement_present=True,
        parcel_expected=True,
        parcel_present=True,
    )

    assert result["state"] == "READY"
    assert result["state"] != "COMPLETED"


def test_idempotency_rejects_short_or_unsafe_values():
    with pytest.raises(ValueError, match="invalid_idempotency_key"):
        spine._idempotency("short")
    with pytest.raises(ValueError, match="invalid_idempotency_key"):
        spine._idempotency("bad key with spaces")

    assert spine._idempotency("market-order:12345678") == "market-order:12345678"


def test_migration_is_checksum_gated_and_not_auto_applied():
    sql = spine.migration_sql()

    assert spine.MARKET_TRANSACTION_MIGRATION_VERSION in sql
    assert spine.MARKET_TRANSACTION_MIGRATION_CHECKSUM in sql
    assert len(spine.MARKET_TRANSACTION_MIGRATION_CHECKSUM) == 64
    assert "oap_schema_migrations" in sql


def test_platform_status_keeps_live_and_external_claims_locked():
    status = spine.platform_status()

    assert status["component"] == "OAP Market Transaction Spine"
    assert status["correlation_authored"] is True
    assert status["payment_capture_performed"] is False
    assert status["money_transfer_performed"] is False
    assert status["external_fulfilment_performed"] is False
    assert status["carrier_handoff_performed"] is False
    assert status["automatic_dispatch_performed"] is False
    assert status["live_database_migration_proven"] is False
    assert status["live_runtime_readback_proven"] is False
    assert status["human_authority_final"] is True
