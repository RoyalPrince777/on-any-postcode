import json
import os


def _restore_configured_authority_once(server):
    if (
        os.environ.get("OAP_RESTORE_CONFIGURED_AUTHORITY_ON_START", "")
        .strip()
        .lower()
        != "true"
    ):
        return

    result = {
        "event": "oap_founder_authority_restore",
        "attempted": True,
        "restored": False,
        "active_level_zero": False,
        "approval_permission": False,
        "secret_exposed": False,
        "error": None,
    }
    try:
        from mission_control import authority, postgres_db

        identity = authority.configured_identity()
        if not identity:
            result["error"] = "identity_selector_unconfigured"
        else:
            with postgres_db.connect() as connection:
                record = authority.sync_authenticated_identity(
                    connection,
                    identity_id=identity,
                    email="",
                    display_name="OAP Founder",
                    email_verified=False,
                )
            result["active_level_zero"] = bool(record.get("is_human_authority"))
            result["approval_permission"] = (
                authority.APPROVAL_PERMISSION in tuple(record.get("permissions") or ())
            )
            result["restored"] = bool(
                result["active_level_zero"] and result["approval_permission"]
            )
    except Exception:
        result["error"] = "restore_failed"

    server.log.info(json.dumps(result, separators=(",", ":")))


def _emit_database_certification(server):
    if os.environ.get("OAP_DB_CERTIFICATION_MODE", "").strip().lower() != "read_only":
        return
    try:
        from mission_control.database_certification import certification_snapshot

        snapshot = certification_snapshot()
    except Exception:
        snapshot = {
            "event": "oap_smi_database_certification",
            "configured": bool(os.environ.get("DATABASE_URL", "").strip()),
            "reachable": False,
            "initialized": False,
            "error": "certification_probe_failed",
            "secret_exposed": False,
        }
    server.log.info(json.dumps(snapshot, separators=(",", ":")))


def _emit_database_connection_diagnostic(server):
    if os.environ.get("OAP_DB_CERTIFICATION_MODE", "").strip().lower() != "read_only":
        return
    try:
        from mission_control.database_connection_diagnostic import diagnostic_snapshot

        snapshot = diagnostic_snapshot()
    except Exception:
        snapshot = {
            "event": "oap_smi_database_connection_diagnostic",
            "configured": bool(os.environ.get("DATABASE_URL", "").strip()),
            "reachable": False,
            "category": "diagnostic_probe_failed",
            "secret_exposed": False,
        }
    server.log.info(json.dumps(snapshot, separators=(",", ":")))


def _emit_smi_function_health(worker):
    """Log a secret-free read-only SMI proof summary after the OAP worker loads."""

    if os.environ.get("RENDER_SERVICE_NAME", "").strip().casefold() == "oap-smi":
        return

    snapshot = {
        "event": "oap_smi_function_health",
        "expected_count": 13,
        "available_count": 0,
        "availability_percent": 0.0,
        "proof_checked_count": 0,
        "proof_coverage_percent": 0.0,
        "runtime_ready_count": 0,
        "runtime_ready_percent": 0.0,
        "whole_smi_green": False,
        "duplicate_primary_paths": None,
        "execution_granted": False,
        "secret_exposed": False,
        "error": None,
    }
    try:
        from app import app as flask_app
        from mission_control.smi_function_health import function_health

        health = function_health(flask_app.url_map)
        snapshot.update(
            expected_count=int(health.get("expected_count") or 0),
            available_count=int(health.get("available_count") or 0),
            availability_percent=float(health.get("availability_percent") or 0.0),
            proof_checked_count=int(health.get("proof_checked_count") or 0),
            proof_coverage_percent=float(health.get("proof_coverage_percent") or 0.0),
            runtime_ready_count=int(health.get("runtime_ready_count") or 0),
            runtime_ready_percent=float(health.get("runtime_ready_percent") or 0.0),
            whole_smi_green=bool(health.get("whole_smi_green")),
            duplicate_primary_paths=int(health.get("duplicate_primary_paths") or 0),
            execution_granted=False,
        )
    except Exception:
        snapshot["error"] = "function_health_probe_failed"

    worker.log.info(json.dumps(snapshot, separators=(",", ":")))


def on_starting(server):
    server.log.info(
        json.dumps(
            {
                "event": "oap_smi_database_binding_probe",
                "database_configured": bool(os.environ.get("DATABASE_URL", "").strip()),
                "render_api_configured": bool(
                    os.environ.get("OAP_RENDER_API_KEY", "").strip()
                    or os.environ.get("RENDER_API_KEY", "").strip()
                ),
                "identity_selector_configured": bool(
                    os.environ.get("OAP_HUMAN_AUTHORITY_ID", "").strip()
                ),
                "email_selector_configured": bool(
                    os.environ.get("OAP_HUMAN_AUTHORITY_EMAIL", "").strip()
                ),
                "secret_exposed": False,
            },
            separators=(",", ":"),
        )
    )
    _emit_database_certification(server)
    _emit_database_connection_diagnostic(server)
    _restore_configured_authority_once(server)


def post_worker_init(worker):
    _emit_smi_function_health(worker)


def post_request(worker, req, environ, resp):
    """Re-check Function Health once local observability has a real health sample."""

    global _FUNCTION_HEALTH_AFTER_HEALTH_EMITTED
    if _FUNCTION_HEALTH_AFTER_HEALTH_EMITTED:
        return
    if str(environ.get("PATH_INFO") or "") != "/healthz":
        return
    status = str(getattr(resp, "status", "") or "")
    if not status.startswith("200"):
        return
    with _FUNCTION_HEALTH_AFTER_HEALTH_LOCK:
        if _FUNCTION_HEALTH_AFTER_HEALTH_EMITTED:
            return
        _emit_smi_function_health(worker)
        _FUNCTION_HEALTH_AFTER_HEALTH_EMITTED = True
