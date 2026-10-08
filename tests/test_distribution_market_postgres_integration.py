from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

from mission_control import (
    arena_rooms,
    bank_authorisation_store,
    commerce_install,
    distribution_market_links,
    founder_private_pod_orders,
    market_supplier_network,
    movement_operations,
    music_civilization_migration,
    music_evidence,
    music_market_purchase,
    pod_provider_registry,
    postgres_db,
    product_cores,
    supplier_bridge,
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



def test_real_postgres_supplier_network_migration_and_no_stock_order_lock():
    """Exercise the Supplier Network migration and fail-closed order gate on real PostgreSQL."""

    postgres_db.init_postgres(assume_yes=True)
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "0009_oap_market_supplier_network.sql"
    ).read_text(encoding="utf-8")
    with postgres_db.connect() as connection:
        for statement in migration.split(";"):
            if statement.strip():
                connection.execute(statement)
        connection.commit()

    seller = str(uuid4())
    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO users(id,email,username,display_name,status)
               VALUES (%s,%s,%s,%s,'active')""",
            (
                seller,
                f"{seller}@example.invalid",
                f"supplier-{seller[:8]}",
                "Supplier Seller",
            ),
        )
        connection.commit()

    created = market_supplier_network.STORE.create_made_to_order_product(
        seller_identity_id=seller,
        name="CI made-to-order hoodie",
        description="ephemeral supplier proof",
        price="50.00",
        garment_type="hoodie",
        artwork_reference="ci-artwork-ref",
        placements=["front"],
        colors=["black"],
        sizes=["M", "L"],
        supplier_slug="tapstitch",
        supplier_label="Tapstitch",
        supplier_product_ref="ci-supplier-product",
        supplier_variant_ref="ci-variant",
        evidence_reference="ci-internal-mapping-evidence",
    )
    assert created["made_to_order"] is True
    assert created["state"] == "DRAFT"
    assert created["order_intent_allowed"] is False
    assert created["supplier_api_called"] is False
    assert created["external_order_created"] is False

    draft_gate = market_supplier_network.STORE.order_intent_allowed(
        product_id=created["product_id"]
    )
    assert draft_gate["allowed"] is False
    assert draft_gate["supplier_managed"] is True
    assert draft_gate["reason"] == "product_not_public"

    ready = market_supplier_network.STORE.mark_ready(
        seller_identity_id=seller,
        product_id=created["product_id"],
        evidence_reference="ci-review-ready-evidence",
    )
    assert ready["state"] == "READY"
    assert ready["order_intent_allowed"] is False
    assert ready["public_listing_active"] is False
    assert ready["provider_execution_enabled"] is False

    ready_gate = market_supplier_network.STORE.order_intent_allowed(
        product_id=created["product_id"]
    )
    assert ready_gate["allowed"] is False
    assert ready_gate["reason"] == "product_not_public"
    assert ready_gate["provider_execution_enabled"] is False
    assert ready_gate["external_execution_allowed"] is False
    assert ready_gate["payment_capture_allowed"] is False

    public = market_supplier_network.STORE.public_projection(
        product_ids=[created["product_id"]]
    )[created["product_id"]]
    assert public["made_to_order"] is True
    assert public["garment_type"] == "hoodie"
    assert public["supplier_identity_public"] is False
    assert "manufacturer" not in public
    assert public["provider_execution_enabled"] is False
    assert public["public_listing_active"] is False
    assert public["order_intent_allowed"] is False

    # A later, separately approved public release may activate the product.
    with postgres_db.connect() as connection:
        connection.execute(
            "UPDATE products SET active=TRUE WHERE id=%s AND seller_id=%s",
            (created["product_id"], seller),
        )
        connection.commit()

    launched_gate = market_supplier_network.STORE.order_intent_allowed(
        product_id=created["product_id"]
    )
    assert launched_gate["allowed"] is True
    assert launched_gate["reason"] is None
    assert launched_gate["public_listing_active"] is True

    launched_public = market_supplier_network.STORE.public_projection(
        product_ids=[created["product_id"]]
    )[created["product_id"]]
    assert launched_public["public_listing_active"] is True
    assert launched_public["order_intent_allowed"] is True

    product_cores.init_product_core_schema(assume_yes=True)
    buyer = str(uuid4())
    order = str(uuid4())
    fulfilment = str(uuid4())
    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO users(id,email,username,display_name,status)
               VALUES (%s,%s,%s,%s,'active')""",
            (
                buyer,
                f"{buyer}@example.invalid",
                f"buyer-{buyer[:8]}",
                "Bridge Buyer",
            ),
        )
        connection.execute(
            """INSERT INTO oap_commerce_orders(
                   order_id,buyer_identity_id,seller_identity_id,state,currency,
                   subtotal_minor,idempotency_key)
               VALUES (%s,%s,%s,'PAYMENT_PROVIDER_REQUIRED','GBP',5000,%s)""",
            (order, buyer, seller, f"bridge-{order[:8]}"),
        )
        connection.execute(
            """INSERT INTO oap_commerce_order_items(
                   order_id,product_id,quantity,unit_price_minor,product_name)
               VALUES (%s,%s,1,5000,'CI made-to-order hoodie')""",
            (order, created["product_id"]),
        )
        connection.execute(
            """INSERT INTO oap_commerce_fulfilment_intents(
                   fulfilment_id,order_id,state)
               VALUES (%s,%s,'PROVIDER_REQUIRED')""",
            (fulfilment, order),
        )
        connection.commit()

    candidate = supplier_bridge.handoff_candidate(order_id=order)
    assert candidate["provider_slug"] == "tapstitch"
    assert candidate["supplier_product_ref"] == "ci-supplier-product"
    assert candidate["supplier_variant_ref"] == "ci-variant"
    assert candidate["bridge_ready"] is False
    assert candidate["checks"]["supplier_ready"] is True
    assert candidate["checks"]["design_ready"] is True
    assert candidate["checks"]["delivery_destination_present"] is False
    assert candidate["checks"]["payment_capture_proven"] is False
    assert candidate["checks"]["provider_connector_authorized"] is False
    assert candidate["external_submission_allowed"] is False
    assert candidate["external_submission_performed"] is False
    assert len(candidate["checks"]) == 21

    stopped = market_supplier_network.STORE.stop(
        seller_identity_id=seller,
        product_id=created["product_id"],
        reason="ci-stop",
    )
    assert stopped["state"] == "STOPPED"
    assert stopped["order_intent_allowed"] is False
    assert stopped["external_execution_allowed"] is False



def test_real_postgres_bank_authorisation_evidence_is_append_only_and_fail_closed():
    postgres_db.init_postgres(assume_yes=True)
    schema = bank_authorisation_store.init_schema(assume_yes=True)
    assert schema["schema_ready"] is True

    draft = bank_authorisation_store.record_evidence(
        category="legal_entity_and_ownership",
        status="DRAFT",
        evidence_reference="ci-company-proof-draft",
    )
    assert draft["regulated_execution_enabled"] is False

    reviewed = bank_authorisation_store.record_evidence(
        category="legal_entity_and_ownership",
        status="ACCEPTED",
        evidence_reference="ci-company-proof-reviewed",
        reviewed_by="ci-founder-review",
    )
    assert reviewed["regulator_authorisation_granted"] is False

    rejected = bank_authorisation_store.record_evidence(
        category="legal_entity_and_ownership",
        status="REJECTED",
        evidence_reference="ci-company-proof-rejected",
        reviewed_by="ci-founder-review",
    )
    assert rejected["regulated_execution_enabled"] is False

    register = bank_authorisation_store.latest_register()
    assert register["legal_entity_and_ownership"]["status"] == "REJECTED"
    assert register["legal_entity_and_ownership"]["proven"] is False

    accepted = bank_authorisation_store.record_evidence(
        category="legal_entity_and_ownership",
        status="ACCEPTED",
        evidence_reference="ci-company-proof-final",
        reviewed_by="ci-founder-review",
    )
    assert accepted["regulated_execution_enabled"] is False

    register = bank_authorisation_store.latest_register()
    assert register["legal_entity_and_ownership"]["status"] == "ACCEPTED"
    assert register["legal_entity_and_ownership"]["proven"] is True

    readiness = bank_authorisation_store.readiness_status()
    assert readiness["evidence_proven"] == 1
    assert readiness["authorised_bank"] is False
    assert readiness["deposit_taking_enabled"] is False

    with postgres_db.connect(readonly=True) as connection:
        count = connection.execute(
            """SELECT COUNT(*) FROM oap_bank_authorisation_evidence
               WHERE category='legal_entity_and_ownership'"""
        ).fetchone()[0]
    assert int(count) == 4


def test_real_postgres_music_market_purchase_entitlement_and_splits():
    """Prove Music -> Market order -> captured-payment observation -> ownership + split ledger."""
    postgres_db.init_postgres(assume_yes=True)
    migrated = music_civilization_migration.apply(assume_yes=True)
    assert migrated["schema_ready"] is True
    assert music_market_purchase.MIGRATION_VERSION in (
        migrated["applied"] + migrated["existing"]
    )

    seller = str(uuid4())
    buyer = str(uuid4())
    oap_beneficiary = str(uuid4())
    release = str(uuid4())
    product = str(uuid4())
    order = str(uuid4())

    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO users(id,email,username,display_name,status)
               VALUES
               (%s,%s,%s,%s,'active'),
               (%s,%s,%s,%s,'active'),
               (%s,%s,%s,%s,'active')""",
            (
                seller, f"{seller}@example.invalid", f"artist-{seller[:8]}", "Artist",
                buyer, f"{buyer}@example.invalid", f"buyer-{buyer[:8]}", "Buyer",
                oap_beneficiary, f"{oap_beneficiary}@example.invalid",
                f"oap-{oap_beneficiary[:8]}", "OAP",
            ),
        )
        connection.execute(
            """INSERT INTO oap_music_releases(
                   release_id,owner_identity_id,title,release_type,state,rights_status,
                   external_distribution_state,idempotency_key)
               VALUES (%s,%s,'CI Music Purchase','single','PUBLISHED','VERIFIED',
                       'PROVIDER_REQUIRED',%s)""",
            (release, seller, f"release-{release[:8]}"),
        )
        connection.execute(
            """INSERT INTO products(id,seller_id,name,description,price_minor,currency,active)
               VALUES (%s,%s,'CI Music Purchase','ephemeral music purchase proof',100,'GBP',TRUE)""",
            (product, seller),
        )
        connection.commit()

    receipt_store = music_evidence.MusicEvidenceStore()
    receipt = receipt_store.append_receipt(
        owner_identity_id=seller,
        release_id=release,
        evidence_kind="recording_rights",
        evidence_bytes=b"ci-rights-proof",
        source_reference="ci:music:rights",
        authority_reference="ci:human-authority",
        territory="GB",
    )

    linked = music_market_purchase.STORE.link_release_product(
        seller_identity_id=seller,
        release_id=release,
        product_id=product,
        rights_evidence_receipt_id=receipt["receipt_id"],
        split_plan=[
            {
                "beneficiary_identity_id": seller,
                "split_kind": "ARTIST",
                "basis_points": 8500,
            },
            {
                "beneficiary_identity_id": oap_beneficiary,
                "split_kind": "OAP",
                "basis_points": 1500,
            },
        ],
        optional_pay_more=True,
    )
    assert linked["state"] == "READY"
    assert linked["minimum_price_minor"] == 100
    assert linked["payment_capture_performed"] is False

    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO oap_commerce_orders(
                   order_id,buyer_identity_id,seller_identity_id,state,currency,
                   subtotal_minor,idempotency_key)
               VALUES (%s,%s,%s,'PAID','GBP',250,%s)""",
            (order, buyer, seller, f"music-order-{order[:8]}"),
        )
        connection.execute(
            """INSERT INTO oap_commerce_order_items(
                   order_id,product_id,quantity,unit_price_minor,product_name)
               VALUES (%s,%s,1,250,'CI Music Purchase')""",
            (order, product),
        )
        connection.execute(
            """INSERT INTO oap_commerce_payment_intents(
                   order_id,amount_minor,currency,state,provider_reference)
               VALUES (%s,250,'GBP','CAPTURED','ci-external-capture-proof')""",
            (order,),
        )
        connection.commit()

    owned = music_market_purchase.STORE.finalize_captured_order(
        buyer_identity_id=buyer,
        order_id=order,
    )
    assert owned["ownership_granted"] is True
    assert owned["amount_minor"] == 250
    assert owned["payment_capture_performed_here"] is False
    assert owned["payout_performed"] is False
    assert owned["split_state"] == "PAYOUT_PROVIDER_REQUIRED"

    replay = music_market_purchase.STORE.finalize_captured_order(
        buyer_identity_id=buyer,
        order_id=order,
    )
    assert replay["entitlement_id"] == owned["entitlement_id"]

    library = music_market_purchase.STORE.library(buyer_identity_id=buyer)
    assert any(
        row["release_id"] == release
        and row["state"] == "OWNED"
        and row["amount_minor"] == 250
        for row in library
    )

    splits = music_market_purchase.STORE.split_ledger(
        identity_id=seller,
        entitlement_id=owned["entitlement_id"],
    )
    assert len(splits) == 2
    assert sum(row["amount_minor"] for row in splits) == 250
    assert {row["state"] for row in splits} == {"PAYOUT_PROVIDER_REQUIRED"}

    with pytest.raises(PermissionError, match="music_entitlement_not_visible"):
        music_market_purchase.STORE.split_ledger(
            identity_id=str(uuid4()),
            entitlement_id=owned["entitlement_id"],
        )



def test_real_postgres_founder_private_pod_install_snapshot_and_fail_closed(monkeypatch):
    """Install the private POD schema and prove immutable replay + disabled execution."""

    base = postgres_db.init_postgres(assume_yes=True)
    assert base["initialized"] is True

    commerce = product_cores.init_product_core_schema(assume_yes=True)
    assert commerce["schema_ready"] is True

    installed = commerce_install.install(assume_yes=True, dry_run=False)
    private_component = installed["components"]["founder_private_pod_orders"]
    assert private_component["schema_ready"] is True
    assert private_component["order_table_ready"] is True
    assert private_component["external_execution_enabled_here"] is False

    owner = str(uuid4())
    seller = str(uuid4())
    product = str(uuid4())
    other_product = str(uuid4())
    key = f"pod-private-{uuid4().hex[:16]}"

    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO users(id,email,username,display_name,status)
               VALUES (%s,%s,%s,%s,'active'),(%s,%s,%s,%s,'active')""",
            (
                owner,
                f"{owner}@example.invalid",
                f"owner-{owner[:8]}",
                "Founder POD Owner",
                seller,
                f"{seller}@example.invalid",
                f"seller-{seller[:8]}",
                "Founder POD Seller",
            ),
        )
        connection.execute(
            """INSERT INTO products(id,seller_id,name,description,price_minor,currency,active)
               VALUES
               (%s,%s,'Private POD A','CI private POD proof',2500,'GBP',FALSE),
               (%s,%s,'Private POD B','CI private POD proof',2500,'GBP',FALSE)""",
            (product, seller, other_product, seller),
        )
        connection.commit()

    canonical = {
        "quantity": 1,
        "supplier_product_ref": "prodigi-sku-ci",
        "supplier_variant_ref": "4011",
        "artwork_reference": "https://example.invalid/artwork.png",
        "color": "Black",
        "size": "M",
        "destination_country": "GB",
    }
    provider_payload = {
        "recipient": {"name": "Founder"},
        "items": [{"sku": "prodigi-sku-ci", "copies": 1}],
    }

    created = founder_private_pod_orders.STORE.create_snapshot(
        owner_identity_id=owner,
        product_id=product,
        provider_id="prodigi",
        canonical_order=canonical,
        provider_payload=provider_payload,
        idempotency_key=key,
    )
    assert created["provider_id"] == "prodigi"
    assert created["provider_reference"] == ""
    assert created["provider_state"] == "PLANNED"
    assert created["public_merchant_access"] is False

    replay = founder_private_pod_orders.STORE.create_snapshot(
        owner_identity_id=owner,
        product_id=product,
        provider_id="prodigi",
        canonical_order={**canonical, "quantity": 99},
        provider_payload={"items": [{"sku": "tampered", "copies": 99}]},
        idempotency_key=key,
    )
    assert replay["private_order_id"] == created["private_order_id"]
    assert replay["canonical_order"] == canonical
    assert replay["provider_payload"] == provider_payload

    with pytest.raises(ValueError, match="private_pod_idempotency_conflict"):
        founder_private_pod_orders.STORE.create_snapshot(
            owner_identity_id=owner,
            product_id=product,
            provider_id="printful",
            canonical_order=canonical,
            provider_payload={"items": [{"variant_id": 4011, "quantity": 1}]},
            idempotency_key=key,
        )

    with pytest.raises(ValueError, match="private_pod_idempotency_conflict"):
        founder_private_pod_orders.STORE.create_snapshot(
            owner_identity_id=owner,
            product_id=other_product,
            provider_id="prodigi",
            canonical_order=canonical,
            provider_payload=provider_payload,
            idempotency_key=key,
        )

    for env_name in (
        "OAP_POD_PROVIDER_ID",
        "OAP_POD_PROVIDER_BASE_URL",
        "OAP_POD_PROVIDER_ALLOWED_HOST",
        "OAP_POD_PROVIDER_TOKEN",
        "OAP_POD_PROVIDER_EXECUTION_ENABLED",
        "OAP_POD_PRODIGI_BASE_URL",
        "OAP_POD_PRODIGI_ALLOWED_HOST",
        "OAP_POD_PRODIGI_TOKEN",
        "OAP_POD_PRODIGI_EXECUTION_ENABLED",
        "OAP_POD_PRINTFUL_BASE_URL",
        "OAP_POD_PRINTFUL_ALLOWED_HOST",
        "OAP_POD_PRINTFUL_TOKEN",
        "OAP_POD_PRINTFUL_EXECUTION_ENABLED",
    ):
        monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(RuntimeError, match="prodigi_execution_disabled"):
        pod_provider_registry.submit(
            provider_id=created["provider_id"],
            payload=created["provider_payload"],
            idempotency_key=created["idempotency_key"],
        )

    with pytest.raises(RuntimeError, match="printful_execution_disabled"):
        pod_provider_registry.submit(
            provider_id="printful",
            payload={"recipient": {}, "items": []},
            idempotency_key=f"{key}-pf",
        )

    after = founder_private_pod_orders.STORE.read_for_owner(
        owner_identity_id=owner,
        private_order_id=created["private_order_id"],
    )
    assert after["provider_reference"] == ""
    assert after["provider_state"] == "PLANNED"

    with postgres_db.connect(readonly=True) as connection:
        receipt_count = connection.execute(
            """SELECT COUNT(*) FROM oap_commerce_provider_receipts
               WHERE subject_id=%s""",
            (created["private_order_id"],),
        ).fetchone()
    assert int(receipt_count[0]) == 0
