import json
import os


def _restore_configured_authority_once(server):
    if os.environ.get("OAP_RESTORE_CONFIGURED_AUTHORITY_ON_START", "").strip().lower() != "true":
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
    _restore_configured_authority_once(server)
