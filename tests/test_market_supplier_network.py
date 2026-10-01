from __future__ import annotations

from pathlib import Path

import app as app_module
from mission_control import market_supplier_network


def _root() -> Path:
    return Path(app_module.app.root_path)


def test_supplier_network_truth_keeps_oap_front_door_and_execution_locked():
    truth = market_supplier_network.truth_status()

    assert truth["canonical_front_door"] == "OAP Market"
    assert truth["supports_oap_owned_products"] is True
    assert truth["supports_certified_public_merchants"] is True
    assert truth["supports_made_to_order_products"] is True
    assert truth["inventory_required_by_oap"] is False
    assert "tapstitch" in truth["supplier_examples"]
    assert truth["supplier_api_called"] is False
    assert truth["external_order_created"] is False
    assert truth["payment_capture_performed"] is False
    assert truth["money_transfer_performed"] is False
    assert truth["sika_settlement_remains_separate"] is True
    assert truth["provider_adapter_required_for_execution"] is True
    assert truth["human_authority_final"] is True


def test_supplier_store_has_atomic_design_mapping_stop_and_order_gate_without_execution_methods():
    methods = set(dir(market_supplier_network.SupplierNetworkStore))

    assert {
        "create_made_to_order_product",
        "bind_product",
        "mark_ready",
        "stop",
        "owner_bindings",
        "public_projection",
        "order_intent_allowed",
    } <= methods

    forbidden = {
        "place_supplier_order",
        "call_supplier_api",
        "capture_payment",
        "transfer_money",
        "dispatch",
        "handoff_to_carrier",
    }
    assert forbidden.isdisjoint(methods)


def test_made_to_order_creation_is_one_database_transaction():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")
    section = source.split("def create_made_to_order_product", 1)[1].split(
        "    def bind_product", 1
    )[0]

    assert "with postgres_db.connect() as connection:" in section
    assert "INSERT INTO products(" in section
    assert "INSERT INTO oap_market_supplier_bindings(" in section
    assert "INSERT INTO oap_market_design_products(" in section
    assert section.count("connection.commit()") == 1
    assert '"order_intent_allowed": False' in section
    assert '"external_order_created": False' in section


def test_supplier_schema_is_product_and_seller_scoped():
    migration = (
        _root() / "migrations" / "0009_oap_market_supplier_network.sql"
    ).read_text(encoding="utf-8")

    assert "oap_market_supplier_bindings" in migration
    assert "oap_market_design_products" in migration
    assert "REFERENCES products(id)" in migration
    assert "REFERENCES users(id)" in migration
    assert "UNIQUE(product_id)" in migration
    assert "made_to_order BOOLEAN NOT NULL DEFAULT TRUE" in migration
    assert "RECOVERY_REQUIRED" in migration


def test_read_only_supplier_paths_do_not_attempt_schema_mutation():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")
    owner = source.split("def owner_bindings", 1)[1].split(
        "    def public_projection", 1
    )[0]
    public = source.split("def public_projection", 1)[1].split(
        "    def order_intent_allowed", 1
    )[0]
    gate = source.split("def order_intent_allowed", 1)[1].split(
        "\n\nSTORE =", 1
    )[0]

    for section in (owner, public, gate):
        assert "connect(readonly=True)" in section
        assert "_ensure_schema(connection)" not in section
        assert "CREATE TABLE" not in section


def test_public_projection_discloses_safe_manufacturing_state_not_private_supplier_refs():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")
    section = source.split("def public_projection", 1)[1].split(
        "    def order_intent_allowed", 1
    )[0]

    assert '"manufacturer"' not in section
    assert '"fulfilment_state"' in section
    assert '"supplier_identity_public": False' in section
    assert '"provider_execution_enabled": False' in section
    assert '"made_to_order"' in section
    assert '"garment_type"' in section
    assert '"colors"' in section
    assert '"sizes"' in section
    assert "supplier_product_ref" not in section
    assert "supplier_variant_ref" not in section
    assert '"external_execution_allowed": False' in section


def test_market_ui_supports_no_stock_design_products_and_locks_draft_supplier_orders():
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")
    app_source = (_root() / "app.py").read_text(encoding="utf-8")

    assert "Made-to-order clothing / print supplier" in template
    assert "No OAP stock is required" in template
    assert 'name="made_to_order"' in template
    assert 'name="artwork_reference"' in template
    assert 'name="supplier_label"' in template
    assert "Supplier execution not yet proven · ordering locked" in template
    assert "Manufacturer ·" not in template
    assert "market_supplier_projection" in template

    assert "create_made_to_order_product(" in app_source
    assert "market_supplier_network.STORE.public_projection(" in app_source
    assert "made_to_order" in app_source


def test_server_order_paths_cannot_bypass_supplier_readiness():
    source = (
        _root() / "mission_control" / "product_core_views.py"
    ).read_text(encoding="utf-8")

    commerce = source.split('def create_order():', 1)[1].split(
        '@bp.get("/market/suppliers")', 1
    )[0]
    market = source.split('def create_market_order():', 1)[1].split(
        '@bp.get("/market/orders/<order_id>")', 1
    )[0]

    assert "order_intent_allowed(" in commerce
    assert 'if gate.get("allowed") is not True:' in commerce
    assert "order_intent_allowed(" in market
    assert 'if gate.get("allowed") is not True:' in market


def test_supplier_owner_apis_are_certified_and_human_controlled():
    source = (
        _root() / "mission_control" / "product_core_views.py"
    ).read_text(encoding="utf-8")

    assert '@bp.get("/market/suppliers")' in source
    assert '@bp.post("/market/products/<product_id>/supplier-ready")' in source
    assert '@bp.post("/market/products/<product_id>/supplier-stop")' in source
    assert "_require_certified_merchant" in source
    assert "evidence_reference" in source
    assert "market_supplier_network.STORE.stop(" in source


def test_ready_mapping_unlocks_oap_order_only_without_public_supplier_claim():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")

    ready = source.split("def mark_ready", 1)[1].split("    def stop", 1)[0]
    gate = source.split("def order_intent_allowed", 1)[1].split("\n\nSTORE =", 1)[0]

    assert '"order_intent_allowed": True' in ready
    assert '"provider_execution_enabled": False' in ready
    assert '"allowed": ready' in gate
    assert '"external_execution_allowed": False' in gate
    assert '"payment_capture_allowed": False' in gate
    assert '"supplier_identity_public": False' in source



def test_supplier_schema_status_is_read_only_and_fails_closed():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")
    section = source.split("def schema_status", 1)[1].split(
        "def init_schema", 1
    )[0]

    assert "connect(readonly=True)" in section
    assert "CREATE TABLE" not in section
    assert "_ensure_schema(" not in section
    assert '"schema_ready": False' in section
    assert '"provider_execution_enabled": False' in section


def test_runtime_emits_private_supplier_schema_readiness_receipt():
    gunicorn_source = (
        _root() / "gunicorn.conf.py"
    ).read_text(encoding="utf-8")

    assert "oap_market_supplier_schema_readiness" in gunicorn_source
    assert "schema_status()" in gunicorn_source
    assert '"human_authority_final": True' in gunicorn_source



def test_supplier_readiness_receipt_uses_production_gunicorn_hook_once():
    root = _root()
    gunicorn_source = (root / "gunicorn.conf.py").read_text(encoding="utf-8")
    init_source = (root / "mission_control" / "__init__.py").read_text(
        encoding="utf-8"
    )

    assert 'event": "oap_market_supplier_schema_readiness"' in gunicorn_source
    assert "schema_status()" in gunicorn_source
    assert "server.log.info(" in gunicorn_source
    assert "oap_market_supplier_schema_readiness" not in init_source



def test_supplier_migration_is_explicit_versioned_and_human_gated():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")

    assert 'SUPPLIER_MIGRATION_VERSION = "0009_oap_market_supplier_network"' in source
    assert "SUPPLIER_MIGRATION_CHECKSUM" in source
    assert "pg_advisory_xact_lock" in source
    assert "Explicit human approval required: pass --yes" in source
    assert "connection.rollback()" in source
    assert "Supplier migration completed without a ready schema" in source
    assert '"provider_execution_enabled": False' in source


def test_supplier_migration_cli_has_status_dry_run_and_explicit_yes():
    source = (
        _root() / "mission_control" / "__init__.py"
    ).read_text(encoding="utf-8")

    assert '@app.cli.command("oap-market-supplier-status")' in source
    assert '@app.cli.command("oap-init-market-supplier")' in source
    assert '@click.option("--dry-run", is_flag=True, default=False)' in source
    assert '@click.option("--yes", "yes", is_flag=True, default=False)' in source
    assert "market_supplier_network.init_schema(" in source


def test_supplier_migration_constants_match_sql_file():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")
    migration = (
        _root() / "migrations" / "0009_oap_market_supplier_network.sql"
    ).read_text(encoding="utf-8")

    for token in (
        "oap_market_supplier_bindings",
        "idx_market_supplier_bindings_seller",
        "idx_market_supplier_bindings_state",
        "oap_market_design_products",
        "idx_market_design_products_seller",
        "RECOVERY_REQUIRED",
    ):
        assert token in source
        assert token in migration



def test_supplier_boot_migration_is_explicit_off_by_default_and_fail_closed():
    source = (_root() / "gunicorn.conf.py").read_text(encoding="utf-8")

    assert "OAP_MARKET_SUPPLIER_MIGRATION_ON_BOOT" in source
    assert '== "true"' in source
    assert "init_schema(assume_yes=True)" in source
    assert "oap_market_supplier_migration_applied" in source
    assert '"provider_execution_enabled": False' in source
    assert "except Exception" not in source[
        source.index('OAP_MARKET_SUPPLIER_MIGRATION_ON_BOOT'):
        source.index('from mission_control.market_supplier_network import schema_status')
    ]



def test_ready_supplier_order_gate_unlocks_oap_intent_only():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")

    assert 'ready = supplier_state == "READY" and design_state == "READY"' in source
    assert '"allowed": ready' in source
    assert '"provider_execution_enabled": False' in source
    assert '"external_execution_allowed": False' in source
    assert '"payment_capture_allowed": False' in source
