"""Mission control package initialiser: registers CLI commands with Flask app."""
from __future__ import annotations

import click
from flask import Flask

from . import audit as auditmod
from . import db as dbmod
from . import (
    movement_operations,
    organism_runtime,
    postgres_db,
    routing,
    surface_security,
)
from .movement_routes import bp as movement_bp
from .provider_views import bp as provider_bp
from .views import bp


def init_app(app: Flask) -> None:
    """Register CLI commands and the Mission Control blueprint."""
    @app.cli.command("oap-db-status")
    @click.option("--json", "json_out", is_flag=True, default=False, help="JSON output")
    def _db_status(json_out: bool) -> None:  # pragma: no cover - CLI wrapper
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
    def _oap_init_db(dry_run: bool, yes: bool) -> None:  # pragma: no cover - CLI wrapper
        dbmod.init_db(dry_run=dry_run, assume_yes=yes)

    @app.cli.command("oap-postgres-status")
    def _oap_postgres_status() -> None:
        import json
        print(json.dumps(postgres_db.postgres_status()))

    @app.cli.command("oap-init-postgres")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", is_flag=True, default=False)
    def _oap_init_postgres(dry_run: bool, yes: bool) -> None:
        import json
        result = postgres_db.init_postgres(dry_run=dry_run, assume_yes=yes)
        print(json.dumps(result))

    @app.cli.command("oap-runtime-status")
    def _oap_runtime_status() -> None:
        import json
        print(json.dumps(organism_runtime.runtime_status()))

    @app.cli.command("oap-init-runtime")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_runtime(dry_run: bool, yes: bool) -> None:
        import json
        result = organism_runtime.init_runtime_schema(
            dry_run=dry_run,
            assume_yes=yes,
        )
        print(json.dumps(result))

    @app.cli.command("oap-movement-status")
    def _oap_movement_status() -> None:
        import json
        print(json.dumps(movement_operations.movement_schema_status()))

    @app.cli.command("oap-init-movement")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--yes", "yes", is_flag=True, default=False)
    def _oap_init_movement(dry_run: bool, yes: bool) -> None:
        import json
        result = movement_operations.init_movement_schema(
            dry_run=dry_run,
            assume_yes=yes,
        )
        print(json.dumps(result))

    @app.cli.command("oap-verify-audit")
    def _oap_verify_audit() -> None:  # pragma: no cover - CLI wrapper
        ok, report = auditmod.verify_audit()
        if ok:
            print("Audit verification: OK")
        else:
            print("Audit verification: FAILED")
            for line in report:
                print(f"  - {line}")

    surface_security.register(app)
    app.register_blueprint(movement_bp)
    app.register_blueprint(provider_bp, url_prefix="/mission")
    app.register_blueprint(bp, url_prefix="/mission")
    routing.startup_probe()
