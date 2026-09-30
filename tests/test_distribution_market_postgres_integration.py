from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

from mission_control import (
    arena_rooms,
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



def test_real_postgres_arena_connect4_multiplayer_create_join_turn_recovery():
    """CI-only ephemeral DB proof; never applies an Arena migration to production."""
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "0008_oap_arena_multiplayer_rooms.sql"
    ).read_text(encoding="utf-8")
    with postgres_db.connect() as connection:
        for statement in migration.split(";"):
            if statement.strip():
                connection.execute(statement)
        connection.commit()

    created = arena_rooms.create_room(
        game_key="connect4", host_name="Arena Alpha", capacity=2
    )
    assert created["status"] == "WAITING"
    joined = arena_rooms.join_room(
        room_code=created["room_code"], display_name="Arena Bravo"
    )
    assert joined["room_id"] == created["room_id"]
    assert joined["seat"] == 2

    host_state = arena_rooms.room_state(
        room_id=created["room_id"], reconnect_token=created["reconnect_token"]
    )
    guest_state = arena_rooms.room_state(
        room_id=joined["room_id"], reconnect_token=joined["reconnect_token"]
    )
    assert host_state["status"] == "ACTIVE"
    assert host_state["your_seat"] == 1
    assert guest_state["your_seat"] == 2
    assert host_state["revision"] == guest_state["revision"] == 0

    with pytest.raises(ValueError, match="arena_room_player_name_taken"):
        arena_rooms.join_room(
            room_code=created["room_code"], display_name="arena alpha"
        )
    with pytest.raises(ValueError, match="arena_room_access_denied"):
        arena_rooms.room_state(
            room_id=created["room_id"], reconnect_token="f" * 40
        )

    first = arena_rooms.connect4_action(
        room_id=created["room_id"],
        reconnect_token=created["reconnect_token"],
        expected_revision=0, request_id="arena-real-host-move-0001",
        action="drop", column=3,
    )
    assert first["revision"] == 1
    assert first["game_state"]["board"][5][3] == 1
    assert first["game_state"]["current_player_id"] == "p2"

    identical = arena_rooms.connect4_action(
        room_id=created["room_id"],
        reconnect_token=created["reconnect_token"],
        expected_revision=0, request_id="arena-real-host-move-0001",
        action="drop", column=3,
    )
    assert identical == {
        "room_id": created["room_id"], "revision": 1, "duplicate": True
    }
    with pytest.raises(ValueError, match="arena_room_idempotency_conflict"):
        arena_rooms.connect4_action(
            room_id=created["room_id"],
            reconnect_token=created["reconnect_token"],
            expected_revision=0, request_id="arena-real-host-move-0001",
            action="drop", column=4,
        )
    with pytest.raises(ValueError, match="arena_room_not_your_turn"):
        arena_rooms.connect4_action(
            room_id=created["room_id"],
            reconnect_token=created["reconnect_token"],
            expected_revision=1, request_id="arena-real-host-move-0002",
            action="drop", column=4,
        )
    with pytest.raises(ValueError, match="arena_room_revision_conflict"):
        arena_rooms.connect4_action(
            room_id=created["room_id"],
            reconnect_token=joined["reconnect_token"],
            expected_revision=0, request_id="arena-real-guest-stale-0001",
            action="drop", column=2,
        )

    second = arena_rooms.connect4_action(
        room_id=created["room_id"],
        reconnect_token=joined["reconnect_token"],
        expected_revision=1, request_id="arena-real-guest-move-0001",
        action="drop", column=4,
    )
    assert second["revision"] == 2
    assert second["game_state"]["board"][5][4] == 2
    recovered = arena_rooms.room_state(
        room_id=created["room_id"], reconnect_token=created["reconnect_token"]
    )
    assert recovered["revision"] == 2
    assert recovered["your_seat"] == 1
    assert recovered["game_state"]["board"][5][3:5] == [1, 2]
    assert "checkpoint" not in recovered["game_state"]

    with pytest.raises(ValueError, match="arena_room_server_game_adapter_required"):
        arena_rooms.update_game_state(
            room_id=created["room_id"],
            reconnect_token=created["reconnect_token"],
            expected_revision=2,
            request_id="arena-real-forged-update-0001",
            game_state={"winner": "forged"},
        )

    stopped = arena_rooms.connect4_action(
        room_id=created["room_id"],
        reconnect_token=created["reconnect_token"],
        expected_revision=2, request_id="arena-real-stop-0001",
        action="stop",
    )
    assert stopped["status"] == "STOPPED"
    terminal = arena_rooms.room_state(
        room_id=created["room_id"], reconnect_token=joined["reconnect_token"]
    )
    assert terminal["status"] == "STOPPED"
    assert terminal["game_state"]["status"] == "stopped"
    with pytest.raises(ValueError, match="arena_room_not_active"):
        arena_rooms.connect4_action(
            room_id=created["room_id"],
            reconnect_token=joined["reconnect_token"],
            expected_revision=3, request_id="arena-real-poststop-0001",
            action="drop", column=5,
        )
