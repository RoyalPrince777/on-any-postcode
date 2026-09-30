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
    property_authority,
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



def test_real_postgres_arena_dot_two_player_scores_replay_and_stop():
    """Exercise the actual Dot scoring engine and room SQL on ephemeral CI DB."""
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

    host = arena_rooms.create_room(game_key="dot", host_name="Dot Alpha", capacity=2)
    guest = arena_rooms.join_room(room_code=host["room_code"], display_name="Dot Bravo")
    assert guest["seat"] == 2
    assert arena_rooms.room_state(
        room_id=host["room_id"], reconnect_token=host["reconnect_token"]
    )["your_seat"] == 1

    moves = [
        (host["reconnect_token"], "0,0", "1,0"),
        (guest["reconnect_token"], "0,0", "0,1"),
        (host["reconnect_token"], "1,0", "1,1"),
        (guest["reconnect_token"], "0,1", "1,1"),
    ]
    for index, (token, a, b) in enumerate(moves):
        result = arena_rooms.dot_action(
            room_id=host["room_id"], reconnect_token=token,
            expected_revision=index, request_id=f"dot-real-move-{index:04d}",
            action="draw", a=a, b=b,
        )
        assert result["revision"] == index + 1
    assert result["game_state"]["boxes"] == {"0,0": "p2"}
    assert result["game_state"]["players"][1]["score"] == 1
    assert result["game_state"]["turn_player_id"] == "p2"

    replay = arena_rooms.dot_action(
        room_id=host["room_id"], reconnect_token=guest["reconnect_token"],
        expected_revision=3, request_id="dot-real-move-0003",
        action="draw", a="0,1", b="1,1",
    )
    assert replay["duplicate"] is True
    assert replay["revision"] == 4
    with pytest.raises(ValueError, match="arena_room_idempotency_conflict"):
        arena_rooms.dot_action(
            room_id=host["room_id"], reconnect_token=guest["reconnect_token"],
            expected_revision=3, request_id="dot-real-move-0003",
            action="draw", a="0,0", b="0,1",
        )
    with pytest.raises(ValueError, match="arena_room_not_your_turn"):
        arena_rooms.dot_action(
            room_id=host["room_id"], reconnect_token=host["reconnect_token"],
            expected_revision=4, request_id="dot-real-wrong-turn-0001",
            action="draw", a="1,1", b="2,1",
        )
    recovered = arena_rooms.room_state(
        room_id=host["room_id"], reconnect_token=guest["reconnect_token"]
    )
    assert recovered["game_state"]["players"][1]["score"] == 1
    assert recovered["your_seat"] == 2
    assert len(recovered["game_state"]["edges"]) == 4
    assert "checkpoint" not in recovered["game_state"]

    stopped = arena_rooms.dot_action(
        room_id=host["room_id"], reconnect_token=host["reconnect_token"],
        expected_revision=4, request_id="dot-real-stop-0001", action="stop",
    )
    assert stopped["status"] == "STOPPED"
    assert arena_rooms.room_state(
        room_id=host["room_id"], reconnect_token=guest["reconnect_token"]
    )["status"] == "STOPPED"


def test_real_postgres_property_grant_scope_expiry_revocation_and_reviewer():
    """Ephemeral CI PostgreSQL only: migration is NOT applied to production.

    The test seeds an artificial reviewed grant to exercise read-back behaviour;
    it is not evidence that any real property has been authorised.
    """
    postgres_db.init_postgres(assume_yes=True)
    ddl = (
        Path(__file__).resolve().parents[1]
        / "migrations" / "0009_oap_property_advertising_authority.sql"
    ).read_text(encoding="utf-8")
    publisher, advertiser, reviewer, evidence_id = (str(uuid4()) for _ in range(4))
    with postgres_db.connect() as connection:
        for statement in ddl.split(";"):
            if statement.strip():
                connection.execute(statement)
        for identity, kind in ((publisher, "HUMAN"), (advertiser, "HUMAN"),
                               (reviewer, "HUMAN_AUTHORITY")):
            connection.execute(
                """INSERT INTO oap_identities(identity_id,display_name,identity_type,status)
                   VALUES (%s,'Isolated PostgreSQL proof',%s,'ACTIVE')""",
                (identity, kind),
            )
        connection.execute(
            """INSERT INTO oap_roles(role_id,name,authority_level)
               VALUES ('human_authority','Human Authority',0)
               ON CONFLICT (role_id) DO NOTHING"""
        )
        connection.execute(
            """INSERT INTO oap_permissions(permission_id,description)
               VALUES ('APPROVE_RECOMMENDATION','Level-zero approval')
               ON CONFLICT (permission_id) DO NOTHING"""
        )
        connection.execute(
            """INSERT INTO oap_role_permissions(role_id,permission_id)
               VALUES ('human_authority','APPROVE_RECOMMENDATION')
               ON CONFLICT DO NOTHING"""
        )
        connection.execute(
            """INSERT INTO oap_identity_roles(identity_id,role_id,granted_by)
               VALUES (%s,'human_authority',%s)""", (reviewer, reviewer)
        )
        connection.execute(
            """INSERT INTO oap_property_advertising_authority
               (evidence_id,publisher_id,advertiser_id,property_ref,country,
                grantor_reference,evidence_sha256,activity,reviewed_by,reviewed_at,
                valid_from,valid_until,status)
               VALUES (%s,%s,%s,'proof-property','United Kingdom',
                       'isolated-ci-evidence-only',%s,'ADVERTISE',%s,CURRENT_TIMESTAMP,
                       CURRENT_TIMESTAMP - INTERVAL '1 day',
                       CURRENT_TIMESTAMP + INTERVAL '1 day','ACTIVE')""",
            (evidence_id, publisher, advertiser, "a" * 64, reviewer),
        )
        connection.commit()

    item = {"publisher_id": publisher, "advertiser_id": advertiser,
            "property_ref": "proof-property", "country": "United Kingdom"}
    verify = property_authority.verified_advertising_authority
    assert verify(item, evidence_id) is True
    assert verify({**item, "advertiser_id": str(uuid4())}, evidence_id) is False
    assert verify({**item, "property_ref": "other-property"}, evidence_id) is False
    assert verify({**item, "country": "Ghana"}, evidence_id) is False
    assert verify(item, str(uuid4())) is False

    with postgres_db.connect() as connection:
        connection.execute(
            """UPDATE oap_property_advertising_authority
               SET valid_until=CURRENT_TIMESTAMP - INTERVAL '1 minute'
               WHERE evidence_id=%s""", (evidence_id,),
        )
        connection.commit()
    assert verify(item, evidence_id) is False  # expired at the DB clock

    with postgres_db.connect() as connection:
        connection.execute(
            """UPDATE oap_property_advertising_authority
               SET valid_until=CURRENT_TIMESTAMP + INTERVAL '1 day',
                   status='REVOKED', revoked_at=CURRENT_TIMESTAMP
               WHERE evidence_id=%s""", (evidence_id,),
        )
        connection.commit()
    assert verify(item, evidence_id) is False

    with postgres_db.connect() as connection:
        connection.execute(
            """UPDATE oap_property_advertising_authority
               SET status='ACTIVE', revoked_at=NULL WHERE evidence_id=%s""",
            (evidence_id,),
        )
        connection.execute(
            """UPDATE oap_identities SET status='REVOKED'
               WHERE identity_id=%s""", (reviewer,),
        )
        connection.commit()
    assert verify(item, evidence_id) is False  # stale reviewer approval denied
