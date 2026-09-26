from __future__ import annotations

import os
from uuid import uuid4

import pytest

from mission_control import (
    distribution_market_links,
    movement_operations,
    postgres_db,
    product_cores,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("OAP_REAL_POSTGRES_PROOF") != "1",
    reason="real PostgreSQL proof is CI-gated",
)


def test_real_postgres_order_booking_parcel_persistence_and_recovery():
    base = postgres_db.init_postgres(assume_yes=True)
    assert base["initialized"] is True

    movement = movement_operations.init_movement_schema(assume_yes=True)
    assert movement["schema_ready"] is True

    commerce = product_cores.init_product_core_schema(assume_yes=True)
    assert commerce["schema_ready"] is True

    schema = distribution_market_links.init_link_schema(
        assume_yes=True, dry_run=False
    )
    assert schema["dry_run"] is False

    owner = str(uuid4())
    seller = str(uuid4())
    product = str(uuid4())
    order = str(uuid4())
    booking = str(uuid4())
    parcel = str(uuid4())

    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO users(id,email,username,display_name,status)
               VALUES (%s,%s,%s,%s,'active'),(%s,%s,%s,%s,'active')""",
            (
                owner, f"{owner}@example.invalid", f"buyer-{owner[:8]}", "Buyer",
                seller, f"{seller}@example.invalid", f"seller-{seller[:8]}", "Seller",
            ),
        )
        connection.execute(
            """INSERT INTO products(id,seller_id,name,description,price_minor,currency,active)
               VALUES (%s,%s,'CI proof product','ephemeral postgres proof',100,'GBP',TRUE)""",
            (product, seller),
        )
        connection.execute(
            """INSERT INTO oap_commerce_orders
               (order_id,buyer_identity_id,seller_identity_id,state,currency,
                subtotal_minor,idempotency_key)
               VALUES (%s,%s,%s,'FULFILMENT_PROVIDER_REQUIRED','GBP',100,%s)""",
            (order, owner, seller, f"order-{order[:8]}"),
        )
        connection.execute(
            """INSERT INTO oap_movement_bookings
               (booking_id,member_identity_id,service_type,pickup,destination,
                state,idempotency_key)
               VALUES (%s,%s,'delivery',%s::jsonb,%s::jsonb,'REQUESTED',%s)""",
            (
                booking,
                owner,
                '{"label":"A","zone":"","latitude":51.4,"longitude":-0.2}',
                '{"label":"B","zone":"","latitude":51.5,"longitude":-0.1}',
                f"booking-{booking[:8]}",
            ),
        )
        connection.execute(
            """INSERT INTO oap_post_office_parcels
               (parcel_id,owner_identity_id,direction,state,oap_tracking_code,
                idempotency_key)
               VALUES (%s,%s,'OUTBOUND','CARRIER_REQUIRED',%s,%s)""",
            (
                parcel,
                owner,
                f"OAP-CI-{parcel[:12]}",
                f"parcel-{parcel[:8]}",
            ),
        )
        connection.commit()

    created = distribution_market_links.create_link(
        owner_identity_id=owner,
        order_id=order,
        booking_id=booking,
        parcel_id=parcel,
    )
    assert created["created"] is True
    assert created["payment_capture_performed"] is False
    assert created["dispatch_performed"] is False
    assert created["carrier_handoff_performed"] is False

    readback = distribution_market_links.read_link(
        owner_identity_id=owner, order_id=order
    )
    assert (readback["order_id"], readback["booking_id"], readback["parcel_id"]) == (
        order,
        booking,
        parcel,
    )

    replay = distribution_market_links.create_link(
        owner_identity_id=owner,
        order_id=order,
        booking_id=booking,
        parcel_id=parcel,
    )
    assert replay["created"] is False

    with pytest.raises(PermissionError, match="canonical_link_not_owned"):
        distribution_market_links.read_link(
            owner_identity_id=str(uuid4()), order_id=order
        )

    # Recovery proof: an uncommitted destructive change is rolled back, and the
    # canonical relationship remains readable afterwards.
    with postgres_db.connect() as connection:
        connection.execute(
            "DELETE FROM oap_distribution_market_links WHERE order_id=%s",
            (order,),
        )
        connection.rollback()

    recovered = distribution_market_links.read_link(
        owner_identity_id=owner, order_id=order
    )
    assert recovered["booking_id"] == booking
    assert recovered["parcel_id"] == parcel
