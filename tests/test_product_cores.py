import pytest

from mission_control import product_cores


def test_product_suite_covers_music_market_and_post_office():
    products = {item["id"]: item for item in product_cores.PRODUCT_SUITE}

    assert set(products) == {"music", "market", "post-office"}
    assert products["music"]["name"] == "OAP Music"
    assert products["music"]["core"] == "OAP Tune Core"
    assert "TuneCore + Spotify-style" in products["music"]["own_equivalent"]
    assert products["market"]["name"] == "OAP Market"
    assert products["market"]["core"] == "OAP Commerce Core"
    assert "Shopify-style" in products["market"]["own_equivalent"]
    assert products["post-office"]["name"] == "OAP Post Office"


def test_external_consequential_edges_are_locked():
    blocked = set(product_cores.BLOCKED_EXTERNAL_ACTIONS)

    assert {
        "external_music_distribution",
        "unlicensed_audio_delivery",
        "royalty_payout",
        "payment_capture",
        "money_transfer",
        "external_fulfilment_handoff",
        "parcel_carrier_handoff",
        "physical_post_office_activation",
    } <= blocked

    forbidden_methods = {
        "capture_payment",
        "pay_royalty",
        "activate_post_office",
        "handoff_to_carrier",
        "distribute_external",
    }
    assert forbidden_methods.isdisjoint(dir(product_cores.PostgresProductCoreStore))


def test_product_core_schema_requires_explicit_human_invocation():
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        product_cores.init_product_core_schema()


def test_product_core_schema_fails_closed_when_base_database_is_not_ready(monkeypatch):
    monkeypatch.setattr(
        product_cores.postgres_db,
        "postgres_status",
        lambda: {"initialized": False},
    )

    status = product_cores.product_core_schema_status()

    assert status["schema_ready"] is False
    assert status["error"] == "base_postgres_not_ready"


def test_product_core_dry_run_is_explicit_and_non_mutating(monkeypatch):
    monkeypatch.setattr(
        product_cores.postgres_db,
        "postgres_status",
        lambda: {"initialized": True},
    )

    result = product_cores.init_product_core_schema(assume_yes=True, dry_run=True)

    assert result["dry_run"] is True
    assert result["migration"] == "0006_music_market_post_office"
    assert result["tables"] == len(product_cores.PRODUCT_CORE_TABLES)
    assert len(result["checksum"]) == 64


def test_platform_status_is_truthful_about_internal_and_external_readiness(monkeypatch):
    monkeypatch.setattr(
        product_cores,
        "product_core_schema_status",
        lambda: {
            "migration": product_cores.PRODUCT_CORE_MIGRATION_VERSION,
            "checksum": product_cores.PRODUCT_CORE_MIGRATION_CHECKSUM,
            "schema_ready": True,
            "tables": len(product_cores.PRODUCT_CORE_TABLES),
            "expected_tables": len(product_cores.PRODUCT_CORE_TABLES),
            "legacy_market_preserved": True,
            "error": None,
        },
    )

    status = product_cores.platform_status()

    assert status["ready"] is True
    assert status["legacy_market_preserved"] is True
    assert status["human_authority_final"] is True
    assert status["independent_external_execution"] is False
    assert all(item["oap_core_ready"] is True for item in status["products"])
    assert all(item["external_edge_ready"] is False for item in status["products"])


def test_commerce_namespace_never_overwrites_legacy_market_tables():
    sql = "\n".join(product_cores.PRODUCT_CORE_SCHEMA_STATEMENTS)

    assert product_cores.LEGACY_MARKET_TABLES == {
        "oap_market_items",
        "oap_market_orders",
    }
    assert "CREATE TABLE IF NOT EXISTS oap_market_orders" not in sql
    assert "CREATE TABLE IF NOT EXISTS oap_market_items" not in sql
    assert "oap_commerce_storefronts" in sql
    assert "oap_commerce_orders" in sql
    assert "oap_commerce_order_items" in sql
    assert "oap_commerce_payment_intents" in sql
    assert "oap_commerce_fulfilment_intents" in sql


def test_schema_contains_durable_first_party_workflows_and_fail_closed_states():
    sql = "\n".join(product_cores.PRODUCT_CORE_SCHEMA_STATEMENTS)

    for table in product_cores.PRODUCT_CORE_TABLES:
        assert table in sql
    assert "MUSIC_CREATOR" in sql
    assert "MARKET_MERCHANT" in sql
    assert "POST_OFFICE_OPERATOR" in sql
    assert "PROVIDER_REQUIRED" in sql
    assert "SELF_DECLARED" in sql
    assert "REVIEW_REQUIRED" in sql
    assert "PLANNED" in sql
    assert "CARRIER_REQUIRED" in sql
    assert "UNIQUE(owner_identity_id,idempotency_key)" in sql
    assert "UNIQUE(buyer_identity_id,idempotency_key)" in sql
    assert "UNIQUE(identity_id,idempotency_key)" in sql
    assert "OAP-KORADASO" in sql
    assert "OAP Koradaso Post Office" in sql
    assert "'Ghana','PLANNED'" in sql
    assert "'ACTIVE'" not in next(
        statement
        for statement in product_cores.PRODUCT_CORE_SCHEMA_STATEMENTS
        if "OAP-KORADASO" in statement
    )
    assert len(product_cores.PRODUCT_CORE_MIGRATION_CHECKSUM) == 64


def test_input_guards_reject_unsafe_or_ambiguous_product_core_values():
    with pytest.raises(ValueError, match="invalid_idempotency_key"):
        product_cores._idempotency("short")
    with pytest.raises(ValueError, match="release_title_required"):
        product_cores._text("", name="release_title", maximum=180)
    with pytest.raises(ValueError, match="release_title_too_long"):
        product_cores._text("x" * 181, name="release_title", maximum=180)
