from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import spot_step2_booking_proof

ROOT = Path(__file__).resolve().parents[1]


def test_step2_proof_fails_closed_when_supply_schema_is_not_ready(monkeypatch):
    monkeypatch.setattr(
        spot_step2_booking_proof.travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": False, "error": "supply_core_schema_pending"},
    )

    with pytest.raises(
        RuntimeError,
        match="supply_core_schema_not_ready:supply_core_schema_pending",
    ):
        spot_step2_booking_proof.run(
            identity_id="00000000-0000-0000-0000-000000000001",
            operation_id="spot-step2-proof-test",
        )


def test_step2_proof_requires_operation_id():
    with pytest.raises(ValueError, match="booking_proof_operation_id_required"):
        spot_step2_booking_proof.run(
            identity_id="00000000-0000-0000-0000-000000000001",
            operation_id="",
        )


def test_step2_proof_is_rollback_only_for_product_rows():
    source = Path(spot_step2_booking_proof.__file__).read_text(encoding="utf-8")

    assert "connection.rollback()" in source
    assert '"product_rows_rolled_back": True' in source
    assert '"real_supplier_created": False' in source
    assert '"real_booking_created": False' in source
    assert '"payment_capture": False' in source
    assert '"pass_issuance": False' in source
    assert '"commission_settlement": False' in source
    assert '"dispatch": False' in source
    assert '"production_state_mutated": False' in source


def test_step2_proof_exercises_full_safe_booking_lifecycle():
    source = Path(spot_step2_booking_proof.__file__).read_text(encoding="utf-8")

    for marker in (
        "step2_quote_proof_failed",
        "step2_hold_proof_failed",
        "PENDING_SUPPLIER_CONFIRMATION",
        "BOUNDED-PROOF-ONLY",
        "step2_supplier_confirmation_proof_failed",
        "step2_supplier_ownership_guard_failed",
        "PROVIDER_REQUIRED",
        "step2_rollback_verification_failed",
    ):
        assert marker in source


def test_step2_proof_persists_only_governed_proof_after_rollback():
    source = Path(spot_step2_booking_proof.__file__).read_text(encoding="utf-8")
    rollback_index = source.index("connection.rollback()")
    receipt_index = source.index("hrm_durable_receipt.build_receipt(")
    audit_index = source.index("approval_service._write_audit(")

    assert rollback_index < receipt_index < audit_index
    assert '"proof_kind": "synthetic_bounded_rollback"' in source
    assert 'action=STEP2_ACTION' in source
    assert "authority.require_human_authority" in source


def test_step2_boot_trigger_is_explicit_and_fail_closed():
    source = (ROOT / "mission_control" / "__init__.py").read_text(encoding="utf-8")

    assert 'OAP_SPOT_STEP2_PROOF_ON_BOOT' in source
    assert 'OAP_SPOT_STEP2_PROOF_OPERATION_ID' in source
    assert "spot_step2_booking_proof.run(" in source
    assert '"event": "oap_spot_step2_booking_proof"' in source
    assert '"real_supplier_created": False' in source
    assert '"real_booking_created": False' in source
    assert '"payment_capture": False' in source
    assert '"dispatch": False' in source


def test_supply_core_boot_migration_is_explicit_and_precedes_step2_proof():
    source = (ROOT / "mission_control" / "__init__.py").read_text(encoding="utf-8")

    assert 'OAP_SUPPLY_CORE_MIGRATION_ON_BOOT' in source
    assert 'travel_supply_core.init_supply_core_schema(' in source
    assert 'assume_yes=True' in source
    assert '"event": "oap_supply_core_migration"' in source
    assert '"human_authority_final": True' in source
    migration_index = source.index('OAP_SUPPLY_CORE_MIGRATION_ON_BOOT')
    step2_index = source.index('OAP_SPOT_STEP2_PROOF_ON_BOOT')
    assert migration_index < step2_index


def test_supply_core_boot_migration_does_not_unlock_payments_or_dispatch():
    source = (ROOT / "mission_control" / "__init__.py").read_text(encoding="utf-8")
    block = source.split('OAP_SUPPLY_CORE_MIGRATION_ON_BOOT', 1)[1].split(
        'OAP_SPOT_STEP2_PROOF_ON_BOOT',
        1,
    )[0]

    assert "payment_capture" not in block
    assert "dispatch" not in block
    assert "execution_granted" not in block
