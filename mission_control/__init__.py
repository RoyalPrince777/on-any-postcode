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
    import click

    from . import audit as auditmod
    from . import db as dbmod
    from . import (
        link_activity,
        link_call_audit,
        link_presence,
        link_relationships,
        link_signalling,
        link_turn,
        link_voice,
        linkup_safety,
        movement_match_safety,
        movement_operations,
        organism_runtime,
        postgres_db,
        product_cores,
        routing,
        surface_security,
        travel_supply_core,
    )
    from .checkpoint_views import bp as checkpoint_bp
    from .founder_tool_views import bp as founder_tool_bp
    from .home_node_views import bp as home_node_bp
    from .humanitarian_views import bp as humanitarian_tracker_bp
    from .isac_views import bp as isac_spatial_bp
    from .link_call_routes import bp as link_call_bp
    from .link_message_routes import bp as link_message_bp
    from .link_presence_routes import bp as link_presence_bp
    from .link_relationship_routes import bp as link_relationship_bp
    from .link_signalling_routes import bp as link_signalling_bp
    from .link_turn_routes import bp as link_turn_bp
    from .link_voice_routes import bp as link_voice_bp
    from .linkup_safety_routes import bp as linkup_safety_bp
    from .movement_routes import bp as movement_bp
    from .oap_data_views import bp as oap_data_bp
    from .product_core_views import bp as product_core_bp
    from .provider_views import bp as provider_bp
    from .travel_supply_views import bp as travel_supply_bp
    from .views import bp

    movement_operations.STORE = movement_match_safety.STORE

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
    def _oap_init_link_signalling(dry_run: bool, yes: bool) -> None:
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

    surface_security.register(app)
    app.register_blueprint(movement_bp)
    app.register_blueprint(linkup_safety_bp)
    app.register_blueprint(link_relationship_bp)
    app.register_blueprint(link_call_bp)
    app.register_blueprint(link_signalling_bp)
    app.register_blueprint(link_turn_bp)
    app.register_blueprint(link_presence_bp)
    app.register_blueprint(link_voice_bp)
    app.register_blueprint(link_message_bp)
    app.register_blueprint(travel_supply_bp)
    app.register_blueprint(provider_bp, url_prefix="/mission")
    app.register_blueprint(product_core_bp, url_prefix="/mission/organs")
    app.register_blueprint(founder_tool_bp, url_prefix="/mission")
    app.register_blueprint(home_node_bp, url_prefix="/mission")
    app.register_blueprint(oap_data_bp, url_prefix="/mission")
    app.register_blueprint(isac_spatial_bp, url_prefix="/mission/isac-spatial")
    app.register_blueprint(humanitarian_tracker_bp, url_prefix="/mission/humanitarian")
    app.register_blueprint(checkpoint_bp, url_prefix="/mission")
    app.register_blueprint(bp, url_prefix="/mission")
    routing.startup_probe()
