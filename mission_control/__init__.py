"""Mission Control package initialiser.

Web-only dependencies are imported inside ``init_app`` so worker-only runtimes
such as the Termux OAP Home Node can import ``mission_control.organism_worker``
without installing Flask, PyJWT crypto extras, or other HTTP surface packages.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def init_app(app: Flask) -> None:
    """Register CLI commands and the Mission Control web surface."""
    import json
    import os

    import click
    from flask import g, request

    from . import audit as auditmod
    from . import (
        authority,
        esim_persistence,
        hrm_durable_receipt,
        link_activity,
        link_call_audit,
        link_ping,
        link_presence,
        link_relationships,
        link_share,
        link_signalling,
        link_turn,
        link_voice,
        link_youth_safety,
        linkup_safety,
        movement_match_safety,
        movement_operations,
        organism_runtime,
        postgres_db,
        product_cores,
        routing,
        smi_auto,
        smi_founder_assets,
        smi_proof_gate,
        spot_step2_booking_proof,
        spot_step3_creator_safety_proof,
        surface_security,
        travel_supply_core,
    )
    from . import db as dbmod
    from .alignment_views import bp as alignment_bp
    from .certification_views import bp as certification_bp
    from .checkpoint_views import bp as checkpoint_bp
    from .founder_tool_views import bp as founder_tool_bp
    from .home_node_views import bp as home_node_bp
    from .humanitarian_views import bp as humanitarian_tracker_bp
    from .isac_views import bp as isac_spatial_bp
    from .link_call_routes import bp as link_call_bp
    from .link_incoming_routes import bp as link_incoming_bp
    from .link_message_routes import bp as link_message_bp
    from .link_ping_routes import bp as link_ping_bp
    from .link_presence_routes import bp as link_presence_bp
    from .link_relationship_routes import bp as link_relationship_bp
    from .link_signalling_routes import bp as link_signalling_bp
    from .link_turn_routes import bp as link_turn_bp
    from .link_voice_routes import bp as link_voice_bp
    from .linkup_safety_routes import bp as linkup_safety_bp
    from .maps_movement_direct_proof_views import bp as maps_movement_direct_proof_bp
    from .membership_revenue import bp as membership_revenue_bp
    from .movement_routes import bp as movement_bp
    from .oap_data_views import bp as oap_data_bp
    from .on_any_place_routes import bp as on_any_place_bp
    from .product_core_views import bp as product_core_bp
    from .provider_views import bp as provider_bp
    from .travel_supply_views import bp as travel_supply_bp
    from .views import bp

    movement_operations.STORE = movement_match_safety.STORE

    if os.environ.get("OAP_ESIM_MIGRATION_ON_BOOT", "").strip() == "1":
        try:
            migration_status = esim_persistence.init_schema(
                postgres_db.connect,
                assume_yes=True,
            )
            print(
                json.dumps(
                    {
                        "event": "oap_esim_migration",
                        "success": True,
                        "schema_ready": migration_status.get("schema_ready") is True,
                        "schema_version": migration_status.get("schema_version"),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception:
            print(
                json.dumps(
                    {
                        "event": "oap_esim_migration",
                        "success": False,
                        "error": "esim_migration_failed",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    supply_migration_requested = (
        os.environ.get("OAP_SUPPLY_CORE_MIGRATION_ON_BOOT", "").strip() == "1"
    )
    if supply_migration_requested:
        try:
            supply_status = travel_supply_core.init_supply_core_schema(
                assume_yes=True
            )
            print(
                json.dumps(
                    {
                        "event": "oap_supply_core_migration",
                        "success": bool(supply_status.get("schema_ready")),
                        "migration": supply_status.get("migration"),
                        "tables": supply_status.get("tables"),
                        "schema_ready": bool(supply_status.get("schema_ready")),
                        "production_state_mutated": True,
                        "human_authority_final": True,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception as exc:
            reason = (
                str(exc)[:220]
                if isinstance(
                    exc,
                    (RuntimeError, ValueError, PermissionError),
                )
                else ""
            )
            print(
                json.dumps(
                    {
                        "event": "oap_supply_core_migration",
                        "success": False,
                        "error": type(exc).__name__,
                        "reason": reason,
                        "human_authority_final": True,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    if os.environ.get("OAP_LINK_MESSAGE_SYNC_MIGRATION_ON_BOOT", "").strip() == "1":
        try:
            sync_status = link_message_sync.init_schema(assume_yes=True)
            print(
                json.dumps(
                    {
                        "event": "oap_link_message_sync_migration",
                        "success": bool(sync_status.get("applied")),
                        "schema_version": sync_status.get("version"),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception:
            print(
                json.dumps(
                    {
                        "event": "oap_link_message_sync_migration",
                        "success": False,
                        "error": "link_message_sync_migration_failed",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    if os.environ.get("OAP_LINK_YOUTH_GUARD_MIGRATION_ON_BOOT", "").strip() == "1":
        try:
            youth_status = link_youth_safety.init_schema(assume_yes=True)
            print(
                json.dumps(
                    {
                        "event": "oap_link_youth_guard_migration",
                        "success": bool(youth_status.get("applied")),
                        "schema_version": youth_status.get("version"),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception:
            print(
                json.dumps(
                    {
                        "event": "oap_link_youth_guard_migration",
                        "success": False,
                        "error": "link_youth_guard_migration_failed",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    try:
        youth_runtime = link_youth_safety.status()
        youth_self_test = youth_runtime.get("policy_self_test") or {}
        print(
            json.dumps(
                {
                    "event": "oap_link_youth_guard_runtime_proof",
                    "ready": bool(youth_runtime.get("ready")),
                    "policy_self_test_passed": bool(
                        youth_self_test.get("passed")
                    ),
                    "cross_age_blocked": bool(
                        youth_self_test.get("cross_age_blocked")
                    ),
                    "same_band_allowed": bool(
                        youth_self_test.get("same_band_allowed")
                    ),
                    "unknown_unresolved": bool(
                        youth_self_test.get("unknown_unresolved")
                    ),
                    "uses_production_identities": False,
                    "stores_date_of_birth": False,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
            flush=True,
        )
    except Exception:
        print(
            json.dumps(
                {
                    "event": "oap_link_youth_guard_runtime_proof",
                    "ready": False,
                    "policy_self_test_passed": False,
                    "uses_production_identities": False,
                    "stores_date_of_birth": False,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
            flush=True,
        )

    if os.environ.get("OAP_LINK_SHARE_MIGRATION_ON_BOOT", "").strip() == "1":
        try:
            share_status = link_share.init_schema(assume_yes=True)
            print(
                json.dumps(
                    {
                        "event": "oap_link_share_migration",
                        "success": bool(share_status.get("applied")),
                        "schema_version": share_status.get("version"),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception:
            print(
                json.dumps(
                    {
                        "event": "oap_link_share_migration",
                        "success": False,
                        "error": "link_share_migration_failed",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    if os.environ.get("OAP_LINK_PING_MIGRATION_ON_BOOT", "").strip() == "1":
        try:
            ping_status = link_ping.init_schema(assume_yes=True)
            print(
                json.dumps(
                    {
                        "event": "oap_link_ping_migration",
                        "success": bool(ping_status.get("applied")),
                        "schema_version": ping_status.get("version"),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception:
            print(
                json.dumps(
                    {
                        "event": "oap_link_ping_migration",
                        "success": False,
                        "error": "link_ping_migration_failed",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    if os.environ.get("OAP_SPOT_STEP2_PROOF_ON_BOOT", "").strip() == "1":
        operation_id = os.environ.get(
            "OAP_SPOT_STEP2_PROOF_OPERATION_ID", ""
        ).strip()
        identity_id = authority.configured_identity()
        try:
            if not operation_id:
                raise RuntimeError("spot_step2_operation_id_not_configured")
            if not identity_id:
                raise RuntimeError("human_authority_identity_not_configured")
            proof = spot_step2_booking_proof.run(
                identity_id=identity_id,
                operation_id=operation_id,
            )
            print(
                json.dumps(
                    {
                        "event": "oap_spot_step2_booking_proof",
                        "success": bool(proof.get("passed")),
                        "quarter": 50,
                        "receipt_verified": bool(proof.get("receipt_verified")),
                        "product_rows_rolled_back": bool(
                            proof.get("product_rows_rolled_back")
                        ),
                        "real_supplier_created": False,
                        "real_booking_created": False,
                        "payment_capture": False,
                        "dispatch": False,
                        "production_state_mutated": False,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001 - proof must fail closed.
            reason = (
                str(exc)[:220]
                if isinstance(
                    exc,
                    (
                        RuntimeError,
                        ValueError,
                        PermissionError,
                        hrm_durable_receipt.ReceiptBlocked,
                    ),
                )
                else ""
            )
            print(
                json.dumps(
                    {
                        "event": "oap_spot_step2_booking_proof",
                        "success": False,
                        "quarter": 50,
                        "error": type(exc).__name__,
                        "reason": reason,
                        "real_supplier_created": False,
                        "real_booking_created": False,
                        "payment_capture": False,
                        "dispatch": False,
                        "production_state_mutated": False,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )

    if os.environ.get("OAP_SPOT_STEP3_PROOF_ON_BOOT", "").strip() == "1":
        operation_id = os.environ.get(
            "OAP_SPOT_STEP3_PROOF_OPERATION_ID", ""
        ).strip()
        identity_id = authority.configured_identity()
        try:
            if not operation_id:
                raise RuntimeError("spot_step3_operation_id_not_configured")
            if not identity_id:
                raise RuntimeError("human_authority_identity_not_configured")
            proof = spot_step3_creator_safety_proof.run(
                identity_id=identity_id,
                operation_id=operation_id,
            )
            print(
                json.dumps(
                    {
                        "event": "oap_spot_step3_creator_safety_proof",
                        "success": bool(proof.get("passed")),
                        "quarter": 75,
                        "receipt_verified": bool(proof.get("receipt_verified")),
                        "creator_routes_proven": bool(
                            proof.get("creator_routes_proven")
                        ),
                        "media_routes_proven": bool(
                            proof.get("media_routes_proven")
                        ),
                        "safety_support_routes_proven": bool(
                            proof.get("safety_support_routes_proven")
                        ),
                        "media_published": False,
                        "external_distribution_performed": False,
                        "public_safeguarding_case_created": False,
                        "execution_authority_expanded": False,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001 - proof must fail closed.
            reason = (
                str(exc)[:220]
                if isinstance(
                    exc,
                    (
                        RuntimeError,
                        ValueError,
                        PermissionError,
                        hrm_durable_receipt.ReceiptBlocked,
                    ),
                )
                else ""
            )
            print(
                json.dumps(
                    {
                        "event": "oap_spot_step3_creator_safety_proof",
                        "success": False,
                        "quarter": 75,
                        "error": type(exc).__name__,
                        "reason": reason,
                        "media_published": False,
                        "external_distribution_performed": False,
                        "public_safeguarding_case_created": False,
                        "execution_authority_expanded": False,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )

    if os.environ.get("OAP_FOUNDER_ASSETS_MIGRATION_ON_BOOT", "").strip() == "1":
        try:
            asset_status = smi_founder_assets.init_schema(assume_yes=True)
            print(
                json.dumps(
                    {
                        "event": "oap_founder_assets_migration",
                        "success": True,
                        "schema_ready": asset_status.get("schema_ready") is True,
                        "migration": asset_status.get("migration"),
                        "raw_content_retained": False,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception:
            print(
                json.dumps(
                    {
                        "event": "oap_founder_assets_migration",
                        "success": False,
                        "error": "founder_assets_migration_failed",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    if os.environ.get("OAP_AEGIS_75_PROOF_ON_BOOT", "").strip() == "1":
        try:
            proof_status = smi_proof_gate.status()
            checks = (
                proof_status.get("checks")
                if isinstance(proof_status, dict)
                else {}
            )
            already_proven = bool(
                isinstance(checks, dict)
                and checks.get("isolation_recovery")
            )
            if already_proven:
                proof = {
                    "passed": True,
                    "already_proven": True,
                    "audit_recorded": True,
                }
            else:
                identity_id = authority.configured_identity()
                if not identity_id:
                    raise RuntimeError("human_authority_identity_not_configured")
                proof = smi_proof_gate.run_isolation_recovery_proof(identity_id)
            print(
                json.dumps(
                    {
                        "event": "oap_aegis_75_proof",
                        "success": bool(proof.get("passed")),
                        "already_proven": bool(proof.get("already_proven")),
                        "audit_recorded": bool(proof.get("audit_recorded")),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception:
            print(
                json.dumps(
                    {
                        "event": "oap_aegis_75_proof",
                        "success": False,
                        "error": "aegis_75_proof_failed",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    @app.cli.command("oap-db-status")
    @click.option("--json", "json_out", is_flag=True, default=False, help="JSON output")
    def _db_status(json_out: bool) -> None:  # pragma: no cover
        res = dbmod.db_status()
        if json_out:
            import json
            print(json.dumps(res))
        else:
            print("OAP Database status:")
            print(f"  Resolved DB path: {res['db_path']}")
            print(f"  Schema migrations applied: {len(res['applied'])}")
            if res['pending']:
                print("  Pending migrations:")
                for migration in res["pending"]:
                    print(f"    - {migration['name']} (checksum: {migration['checksum']})")
            else:
                print("  No pending migrations")

    @app.cli.command("oap-init-db")
    @click.option("--dry-run", "dry_run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_db(dry_run: bool, yes: bool) -> None:  # pragma: no cover
        dbmod.init_db(dry_run=dry_run, assume_yes=yes)

    @app.cli.command("oap-postgres-status")
    def _oap_postgres_status() -> None:
        import json
        print(json.dumps(postgres_db.postgres_status()))

    @app.cli.command("oap-init-postgres")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_postgres(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(postgres_db.init_postgres(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-esim-status")
    def _oap_esim_status() -> None:
        import json
        print(json.dumps(esim_persistence.schema_status(postgres_db.connect)))

    @app.cli.command("oap-init-esim")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_esim(dry_run: bool, yes: bool) -> None:
        import json
        print(
            json.dumps(
                esim_persistence.init_schema(
                    postgres_db.connect,
                    dry_run=dry_run,
                    assume_yes=yes,
                )
            )
        )

    @app.cli.command("oap-founder-assets-status")
    def _oap_founder_assets_status() -> None:
        import json
        print(json.dumps(smi_founder_assets.schema_status()))

    @app.cli.command("oap-init-founder-assets")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_founder_assets(dry_run: bool, yes: bool) -> None:
        import json
        print(
            json.dumps(
                smi_founder_assets.init_schema(
                    dry_run=dry_run,
                    assume_yes=yes,
                )
            )
        )

    @app.cli.command("oap-runtime-status")
    def _oap_runtime_status() -> None:
        import json
        print(json.dumps(organism_runtime.runtime_status()))

    @app.cli.command("oap-init-runtime")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_runtime(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(organism_runtime.init_runtime_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-movement-status")
    def _oap_movement_status() -> None:
        import json
        print(json.dumps(movement_operations.movement_schema_status()))

    @app.cli.command("oap-init-movement")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_movement(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(movement_operations.init_movement_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-linkup-safety-status")
    def _oap_linkup_safety_status() -> None:
        import json
        print(json.dumps(linkup_safety.status()))

    @app.cli.command("oap-init-linkup-safety")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_linkup_safety(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(linkup_safety.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-link-relationships-status")
    def _oap_link_relationships_status() -> None:
        import json
        print(json.dumps(link_relationships.status()))

    @app.cli.command("oap-init-link-relationships")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_relationships(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_relationships.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-link-call-audit-status")
    def _oap_link_call_audit_status() -> None:
        import json
        print(json.dumps(link_call_audit.status()))

    @app.cli.command("oap-init-link-call-audit")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_call_audit(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_call_audit.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-purge-link-call-audit")
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_purge_link_call_audit(yes: bool) -> None:
        if not yes:
            raise click.ClickException("explicit_confirmation_required")
        print(link_call_audit.purge_expired())

    @app.cli.command("oap-link-signalling-status")
    def _oap_link_signalling_status() -> None:
        import json
        print(json.dumps(link_signalling.status()))

    @app.cli.command("oap-init-link-signalling")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_link_signalling(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_signalling.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-purge-link-signalling")
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_purge_link_signalling(yes: bool) -> None:
        if not yes:
            raise click.ClickException("explicit_confirmation_required")
        print(link_signalling.purge_expired())

    @app.cli.command("oap-link-turn-status")
    def _oap_link_turn_status() -> None:
        import json
        print(json.dumps(link_turn.status()))

    @app.cli.command("oap-link-ping-status")
    def _oap_link_ping_status() -> None:
        import json
        print(json.dumps(link_ping.status()))

    @app.cli.command("oap-init-link-ping")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_ping(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_ping.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-link-presence-status")
    def _oap_link_presence_status() -> None:
        import json
        print(json.dumps(link_presence.status()))

    @app.cli.command("oap-init-link-presence")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_presence(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_presence.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-purge-link-presence")
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_purge_link_presence(yes: bool) -> None:
        if not yes:
            raise click.ClickException("explicit_confirmation_required")
        print(link_presence.purge_expired())

    @app.cli.command("oap-link-message-sync-status")
    def _oap_link_message_sync_status() -> None:
        import json
        print(json.dumps(link_message_sync.status()))

    @app.cli.command("oap-init-link-message-sync")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_message_sync(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_message_sync.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-set-link-age-band")
    @click.option("--identity-id", required=True)
    @click.option("--age-band", type=click.Choice(["minor", "adult"]), required=True)
    @click.option(
        "--source",
        type=click.Choice(["verified_record", "human_authority"]),
        default="human_authority",
        show_default=True,
    )
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_set_link_age_band(
        identity_id: str,
        age_band: str,
        source: str,
        yes: bool,
    ) -> None:
        import json
        if not yes:
            raise click.ClickException("explicit_confirmation_required")
        confirmer = authority.configured_identity()
        if not confirmer:
            raise click.ClickException("human_authority_identity_not_configured")
        try:
            result = link_youth_safety.set_age_band(
                identity_id,
                age_band=age_band,
                confirmed_by_identity_id=confirmer,
                source=source,
                human_authority_approved=True,
            )
        except Exception as exc:
            raise click.ClickException(str(exc) or type(exc).__name__) from exc
        print(json.dumps(result))

    @app.cli.command("oap-link-youth-guard-status")
    def _oap_link_youth_guard_status() -> None:
        import json
        print(json.dumps(link_youth_safety.status()))

    @app.cli.command("oap-init-link-youth-guard")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_youth_guard(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_youth_safety.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-link-share-status")
    def _oap_link_share_status() -> None:
        import json
        print(json.dumps(link_share.status()))

    @app.cli.command("oap-init-link-share")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_share(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_share.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-link-voice-status")
    def _oap_link_voice_status() -> None:
        import json
        print(json.dumps(link_voice.status()))

    @app.cli.command("oap-init-link-voice")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_voice(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_voice.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-link-activity-status")
    def _oap_link_activity_status() -> None:
        import json
        print(json.dumps(link_activity.status()))

    @app.cli.command("oap-init-link-activity")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_link_activity(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(link_activity.init_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-purge-link-activity")
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_purge_link_activity(yes: bool) -> None:
        if not yes:
            raise click.ClickException("explicit_confirmation_required")
        print(link_activity.purge_expired())

    @app.cli.command("oap-product-cores-status")
    def _oap_product_cores_status() -> None:
        import json
        print(json.dumps(product_cores.platform_status()))

    @app.cli.command("oap-init-product-cores")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_product_cores(dry_run: bool, yes: bool) -> None:
        import json
        print(json.dumps(product_cores.init_product_core_schema(dry_run=dry_run, assume_yes=yes)))

    @app.cli.command("oap-travel-supply-status")
    def _oap_travel_supply_status() -> None:
        import json
        print(json.dumps(travel_supply_core.status()))

    @app.cli.command("oap-init-travel-supply")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_travel_supply(dry_run: bool, yes: bool) -> None:
        import json
        print(
            json.dumps(
                travel_supply_core.init_supply_core_schema(
                    dry_run=dry_run,
                    assume_yes=yes,
                )
            )
        )

    @app.cli.command("oap-verify-audit")
    def _oap_verify_audit() -> None:  # pragma: no cover
        ok, report = auditmod.verify_audit()
        if ok:
            print("Audit verification: OK")
        else:
            print("Audit verification: FAILED")
            for line in report:
                print(f"  - {line}")

    @app.before_request
    def _oap_smi_auto_observe() -> None:
        """Keep SMI present on every request without model calls or writes."""

        g.oap_smi_auto = smi_auto.observe(
            request.method,
            request.path,
            request.endpoint,
        )

    @app.context_processor
    def _oap_smi_auto_context() -> dict[str, object]:
        return {
            "smi_auto": getattr(g, "oap_smi_auto", smi_auto.public_status())
        }

    @app.after_request
    def _oap_smi_auto_response(response):
        state = getattr(g, "oap_smi_auto", smi_auto.public_status())
        response.headers.setdefault("X-OAP-SMI-Auto", "active")
        response.headers.setdefault("X-OAP-SMI-Mode", str(state.get("mode", "automatic_low_noise")))
        response.headers.setdefault(
            "X-OAP-SMI-War-Room",
            "escalate" if state.get("war_room_escalation") else "normal",
        )
        response.headers.setdefault("X-OAP-SMI-Execution", "blocked")
        return response

    surface_security.register(app)
    app.register_blueprint(on_any_place_bp)
    app.register_blueprint(membership_revenue_bp)
    app.register_blueprint(movement_bp)
    app.register_blueprint(linkup_safety_bp)
    app.register_blueprint(link_relationship_bp)
    app.register_blueprint(link_call_bp)
    app.register_blueprint(link_signalling_bp)
    app.register_blueprint(link_turn_bp)
    app.register_blueprint(link_incoming_bp)
    app.register_blueprint(link_ping_bp)
    app.register_blueprint(link_presence_bp)
    app.register_blueprint(link_voice_bp)
    app.register_blueprint(link_message_bp)
    app.register_blueprint(travel_supply_bp)
    app.register_blueprint(provider_bp, url_prefix="/mission")
    app.register_blueprint(product_core_bp, url_prefix="/mission/organs")
    app.register_blueprint(founder_tool_bp, url_prefix="/mission")
    app.register_blueprint(certification_bp, url_prefix="/mission")
    app.register_blueprint(home_node_bp, url_prefix="/mission")
    app.register_blueprint(oap_data_bp, url_prefix="/mission")
    app.register_blueprint(isac_spatial_bp, url_prefix="/mission/isac-spatial")
    app.register_blueprint(humanitarian_tracker_bp, url_prefix="/mission/humanitarian")
    app.register_blueprint(checkpoint_bp, url_prefix="/mission")
    app.register_blueprint(maps_movement_direct_proof_bp, url_prefix="/mission")
    app.register_blueprint(alignment_bp, url_prefix="/mission")
    app.register_blueprint(bp, url_prefix="/mission")
    routing.startup_probe()