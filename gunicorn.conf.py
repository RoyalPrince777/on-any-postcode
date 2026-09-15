import json
import os


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
