import json
import os


def on_starting(server):
    server.log.info(
        json.dumps(
            {
                "event": "oap_smi_database_binding_probe",
                "database_configured": bool(os.environ.get("DATABASE_URL", "").strip()),
                "secret_exposed": False,
            },
            separators=(",", ":"),
        )
    )
