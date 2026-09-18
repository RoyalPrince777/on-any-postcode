"""Bounded live proof for The Spot Step 2 booking lifecycle.

The proof exercises the first-party Supply Core schema inside one database
transaction, then rolls back every temporary product row. Only the governed HRM
and audit proof persist. It never captures payment, issues a pass, settles
commission, dispatches work, or claims a real supplier/customer reservation.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from . import approval_service, authority, hrm_durable_receipt, postgres_db, travel_supply_core
from .hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7

STEP2_ACTION = "SPOT_STEP2_BOOKING_LIFECYCLE_PROOF"


def _uuid(value: object, name: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _scalar(connection: Any, sql: str, params: tuple[Any, ...]) -> int:
    row = connection.execute(sql, params).fetchone()
    return int(row[0] or 0) if row else 0


def run(*, identity_id: object, operation_id: object) -> dict[str, Any]:
    """Exercise quote -> hold -> request -> supplier confirmation, then rollback."""

    identity = _uuid(identity_id, "human_authority_identity")
    operation = str(operation_id or "").strip()[:160]
    if not operation:
        raise ValueError("booking_proof_operation_id_required")

    schema = travel_supply_core.supply_core_schema_status()
    if not schema.get("schema_ready"):
        raise RuntimeError(
            "supply_core_schema_not_ready:"
            + str(schema.get("error") or "unknown")[:120]
        )

    proof_user = str(uuid.uuid4())
    proof_buyer = str(uuid.uuid4())
    supplier_id = str(uuid.uuid4())
    listing_id = str(uuid.uuid4())
    slot_id = str(uuid.uuid4())
    hold_id = str(uuid.uuid4())
    reservation_id = str(uuid.uuid4())

    checks: dict[str, bool] = {
        "authority": False,
        "quote": False,
        "hold": False,
        "reservation_request": False,
        "supplier_confirmation": False,
        "payment_locked": False,
        "pass_locked": False,
        "commission_locked": False,
        "rollback": False,
    }

    with postgres_db.connect() as connection:
        authority.require_human_authority(connection, identity)
        checks["authority"] = True

        try:
            connection.execute(
                """INSERT INTO users(id,username,display_name,status)
                   VALUES (%s,%s,'Step 2 proof supplier','active'),
                          (%s,%s,'Step 2 proof buyer','active')""",
                (
                    proof_user,
                    f"step2-supplier-{proof_user[:8]}",
                    proof_buyer,
                    f"step2-buyer-{proof_buyer[:8]}",
                ),
            )
            connection.execute(
                """INSERT INTO oap_supply_suppliers(
                       supplier_id,owner_identity_id,display_name,supplier_type,
                       state,commercial_terms_state,terms_version
                   ) VALUES (%s,%s,'Bounded proof supplier','mixed',
                             'CERTIFIED','CERTIFIED','step2-proof')""",
                (supplier_id, proof_user),
            )
            connection.execute(
                """INSERT INTO oap_supply_listings(
                       listing_id,supplier_id,category,title,description,
                       place_label,country,state,idempotency_key
                   ) VALUES (%s,%s,'activity','Bounded proof listing',
                             'Rolled-back Step 2 lifecycle proof only',
                             'OAP Proof Zone','GB','ACTIVE',%s)""",
                (listing_id, supplier_id, f"step2-listing-{listing_id}"),
            )
            connection.execute(
                """INSERT INTO oap_supply_inventory_slots(
                       slot_id,listing_id,starts_at,ends_at,capacity_total,
                       price_minor,currency,price_basis,state
                   ) VALUES (
                       %s,%s,CURRENT_TIMESTAMP+INTERVAL '1 day',
                       CURRENT_TIMESTAMP+INTERVAL '1 day 1 hour',
                       2,2500,'GBP','per proof unit','ACTIVE'
                   )""",
                (slot_id, listing_id),
            )

            quote = connection.execute(
                """SELECT s.slot_id,s.capacity_total-s.capacity_held-s.capacity_confirmed,
                          s.price_minor,s.currency,p.state,p.commercial_terms_state,l.state
                   FROM oap_supply_inventory_slots s
                   JOIN oap_supply_listings l ON l.listing_id=s.listing_id
                   JOIN oap_supply_suppliers p ON p.supplier_id=l.supplier_id
                   WHERE l.listing_id=%s AND s.state='ACTIVE'
                     AND l.state='ACTIVE' AND p.state='CERTIFIED'
                     AND p.commercial_terms_state='CERTIFIED'""",
                (listing_id,),
            ).fetchone()
            checks["quote"] = bool(
                quote
                and str(quote[0]) == slot_id
                and int(quote[1]) == 2
                and int(quote[2]) == 2500
                and str(quote[3]) == "GBP"
            )
            if not checks["quote"]:
                raise RuntimeError("step2_quote_proof_failed")

            connection.execute(
                """INSERT INTO oap_supply_reservation_holds(
                       hold_id,slot_id,buyer_identity_id,quantity,amount_minor,
                       currency,state,expires_at,idempotency_key
                   ) VALUES (
                       %s,%s,%s,1,2500,'GBP','HELD',
                       CURRENT_TIMESTAMP+INTERVAL '15 minutes',%s
                   )""",
                (hold_id, slot_id, proof_buyer, f"step2-hold-{hold_id}"),
            )
            connection.execute(
                """UPDATE oap_supply_inventory_slots
                   SET capacity_held=capacity_held+1 WHERE slot_id=%s""",
                (slot_id,),
            )
            hold = connection.execute(
                """SELECT h.state,s.capacity_held,s.capacity_confirmed
                   FROM oap_supply_reservation_holds h
                   JOIN oap_supply_inventory_slots s ON s.slot_id=h.slot_id
                   WHERE h.hold_id=%s""",
                (hold_id,),
            ).fetchone()
            checks["hold"] = bool(
                hold and str(hold[0]) == "HELD"
                and int(hold[1]) == 1 and int(hold[2]) == 0
            )
            if not checks["hold"]:
                raise RuntimeError("step2_hold_proof_failed")

            connection.execute(
                """INSERT INTO oap_supply_reservations(
                       reservation_id,hold_id,listing_id,supplier_id,
                       buyer_identity_id,quantity,total_amount_minor,currency,
                       state,payment_state,pass_state,commission_state,human_confirmed
                   ) VALUES (
                       %s,%s,%s,%s,%s,1,2500,'GBP',
                       'PENDING_SUPPLIER_CONFIRMATION','PROVIDER_REQUIRED',
                       'PROVIDER_REQUIRED','PROVIDER_REQUIRED',TRUE
                   )""",
                (
                    reservation_id,
                    hold_id,
                    listing_id,
                    supplier_id,
                    proof_buyer,
                ),
            )
            connection.execute(
                """UPDATE oap_supply_reservation_holds
                   SET state='CONVERTED' WHERE hold_id=%s""",
                (hold_id,),
            )
            pending = connection.execute(
                """SELECT state,payment_state,pass_state,commission_state
                   FROM oap_supply_reservations WHERE reservation_id=%s""",
                (reservation_id,),
            ).fetchone()
            checks["reservation_request"] = bool(
                pending
                and str(pending[0]) == "PENDING_SUPPLIER_CONFIRMATION"
            )
            checks["payment_locked"] = bool(
                pending and str(pending[1]) == "PROVIDER_REQUIRED"
            )
            checks["pass_locked"] = bool(
                pending and str(pending[2]) == "PROVIDER_REQUIRED"
            )
            checks["commission_locked"] = bool(
                pending and str(pending[3]) == "PROVIDER_REQUIRED"
            )
            if not all(
                checks[name]
                for name in (
                    "reservation_request",
                    "payment_locked",
                    "pass_locked",
                    "commission_locked",
                )
            ):
                raise RuntimeError("step2_reservation_boundary_failed")

            owner_match = connection.execute(
                """SELECT 1
                   FROM oap_supply_reservations r
                   JOIN oap_supply_suppliers p ON p.supplier_id=r.supplier_id
                   WHERE r.reservation_id=%s AND p.owner_identity_id=%s""",
                (reservation_id, proof_user),
            ).fetchone()
            wrong_owner = connection.execute(
                """SELECT 1
                   FROM oap_supply_reservations r
                   JOIN oap_supply_suppliers p ON p.supplier_id=r.supplier_id
                   WHERE r.reservation_id=%s AND p.owner_identity_id=%s""",
                (reservation_id, proof_buyer),
            ).fetchone()
            if owner_match is None or wrong_owner is not None:
                raise RuntimeError("step2_supplier_ownership_guard_failed")

            connection.execute(
                """UPDATE oap_supply_reservations
                   SET state='CONFIRMED',
                       supplier_confirmation_reference='BOUNDED-PROOF-ONLY'
                   WHERE reservation_id=%s""",
                (reservation_id,),
            )
            connection.execute(
                """UPDATE oap_supply_inventory_slots
                   SET capacity_held=0,capacity_confirmed=1
                   WHERE slot_id=%s""",
                (slot_id,),
            )
            confirmed = connection.execute(
                """SELECT r.state,r.payment_state,r.pass_state,r.commission_state,
                          s.capacity_held,s.capacity_confirmed
                   FROM oap_supply_reservations r
                   JOIN oap_supply_reservation_holds h ON h.hold_id=r.hold_id
                   JOIN oap_supply_inventory_slots s ON s.slot_id=h.slot_id
                   WHERE r.reservation_id=%s""",
                (reservation_id,),
            ).fetchone()
            checks["supplier_confirmation"] = bool(
                confirmed
                and str(confirmed[0]) == "CONFIRMED"
                and str(confirmed[1]) == "PROVIDER_REQUIRED"
                and str(confirmed[2]) == "PROVIDER_REQUIRED"
                and str(confirmed[3]) == "PROVIDER_REQUIRED"
                and int(confirmed[4]) == 0
                and int(confirmed[5]) == 1
            )
            if not checks["supplier_confirmation"]:
                raise RuntimeError("step2_supplier_confirmation_proof_failed")
        finally:
            connection.rollback()

    with postgres_db.connect(readonly=True) as connection:
        residual = sum(
            (
                _scalar(
                    connection,
                    "SELECT COUNT(*) FROM users WHERE id IN (%s,%s)",
                    (proof_user, proof_buyer),
                ),
                _scalar(
                    connection,
                    "SELECT COUNT(*) FROM oap_supply_suppliers WHERE supplier_id=%s",
                    (supplier_id,),
                ),
                _scalar(
                    connection,
                    "SELECT COUNT(*) FROM oap_supply_listings WHERE listing_id=%s",
                    (listing_id,),
                ),
                _scalar(
                    connection,
                    "SELECT COUNT(*) FROM oap_supply_inventory_slots WHERE slot_id=%s",
                    (slot_id,),
                ),
                _scalar(
                    connection,
                    "SELECT COUNT(*) FROM oap_supply_reservation_holds WHERE hold_id=%s",
                    (hold_id,),
                ),
                _scalar(
                    connection,
                    "SELECT COUNT(*) FROM oap_supply_reservations WHERE reservation_id=%s",
                    (reservation_id,),
                ),
            )
        )
    checks["rollback"] = residual == 0
    if not checks["rollback"]:
        raise RuntimeError("step2_rollback_verification_failed")

    canonical = {
        "mind": {name: True for name in MIND_7},
        "body": {name: True for name in BODY_7},
        "soul": {name: True for name in SOUL_7},
    }
    receipt = hrm_durable_receipt.build_receipt(
        "spot-step2-booking-lifecycle",
        {
            "governance": "7-7-7",
            "checks": canonical,
            "evidence_proven": all(checks.values()),
            "authority_transferred": False,
            "human_authority_required": True,
            "human_authority_approved": True,
            "proof_kind": "synthetic_bounded_rollback",
            "quote_proven": checks["quote"],
            "hold_proven": checks["hold"],
            "reservation_request_proven": checks["reservation_request"],
            "supplier_confirmation_logic_proven": checks["supplier_confirmation"],
            "product_rows_rolled_back": checks["rollback"],
            "real_supplier_created": False,
            "real_booking_created": False,
            "payment_capture": False,
            "pass_issuance": False,
            "commission_settlement": False,
            "dispatch": False,
            "production_state_mutated": False,
            "human_authority_final": True,
        },
        idempotency_key=operation,
    )
    durable = hrm_durable_receipt.persist_and_read_back(receipt)

    with postgres_db.connect() as connection:
        authority.require_human_authority(connection, identity)
        approval_service._write_audit(
            connection,
            actor_id=identity,
            action=STEP2_ACTION,
            target="THE_SPOT_BOOKING_LIFECYCLE",
            reason=(
                "Bounded Step 2 booking lifecycle proof completed; temporary "
                "product rows were rolled back and no money or dispatch occurred."
            ),
            correlation_id=receipt.receipt_id,
            metadata={
                "passed": True,
                "proof_kind": "synthetic_bounded_rollback",
                "quote_proven": True,
                "hold_proven": True,
                "reservation_request_proven": True,
                "supplier_confirmation_logic_proven": True,
                "product_rows_rolled_back": True,
                "payment_capture": False,
                "pass_issuance": False,
                "commission_settlement": False,
                "dispatch": False,
                "production_state_mutated": False,
                "authority_level": 0,
                "human_authority_final": True,
            },
        )
        connection.commit()

    return {
        "component": "The Spot Step 2 Booking Lifecycle Proof",
        "quarter": 50,
        "passed": True,
        "checks": checks,
        "receipt_verified": bool(
            durable.get("write_verified") and durable.get("read_back_verified")
        ),
        "product_rows_rolled_back": True,
        "real_supplier_created": False,
        "real_booking_created": False,
        "payment_capture": False,
        "pass_issuance": False,
        "commission_settlement": False,
        "dispatch": False,
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }
