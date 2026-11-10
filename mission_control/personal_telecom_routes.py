"""Protected My Line front door and read-only telecom control routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import personal_telecom, personal_telecom_install, web_security

bp = Blueprint("personal_telecom_ui", __name__, template_folder="templates")

FEATURE_ROUTES: tuple[dict[str, str], ...] = (
    {"id": "phone", "name": "Phone", "route": "/linkup?intent=link-call", "kind": "communications"},
    {"id": "incoming", "name": "Incoming", "route": "/linkup/incoming", "kind": "communications"},
    {"id": "recents", "name": "Recents", "route": "/linkup/calls/recents", "kind": "communications"},
    {"id": "ptt", "name": "PTT", "route": "/ptt", "kind": "communications"},
    {"id": "messages", "name": "Messages", "route": "/linkup?intent=message", "kind": "communications"},
    {"id": "contacts", "name": "Contacts", "route": "/linkup", "kind": "communications"},
    {"id": "my_card", "name": "My Card", "route": "/my-card", "kind": "identity"},
    {"id": "passport", "name": "Network Passport", "route": "/my-line/passport", "kind": "telecom"},
    {"id": "gates", "name": "Unlock Gates", "route": "/my-line/gates", "kind": "telecom"},
    {"id": "install", "name": "Install & Verify", "route": "/my-line/install", "kind": "device"},
    {"id": "recovery", "name": "Recovery", "route": "/my-line/recovery", "kind": "safety"},
    {"id": "status", "name": "My Line Status", "route": "/my-line/status", "kind": "telecom"},
)

BUTTON_GROUPS: tuple[dict[str, object], ...] = (
    {
        "id": "use",
        "name": "Use My Line",
        "buttons": ("phone", "incoming", "recents", "ptt", "messages", "contacts"),
    },
    {
        "id": "control",
        "name": "Line Control",
        "buttons": ("my_card", "passport", "status", "install", "gates", "recovery"),
    },
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def surface_status() -> dict[str, object]:
    telecom = personal_telecom.status()
    install = personal_telecom_install.status()
    return {
        "system": "OAP My Line",
        "front_door": "/my-line",
        "button_count": len(FEATURE_ROUTES),
        "feature_routes": tuple(dict(item) for item in FEATURE_ROUTES),
        "button_groups": BUTTON_GROUPS,
        "services": telecom["line"]["services"],
        "network_passport": {
            "status": telecom["line"]["network_passport"]["status"],
            "credential_material_exposed": False,
        },
        "install": {
            "installer_built": install["installer_built"],
            "software_ready": install["software_ready"],
            "manifest_present": install["manifest_present"],
            "external_activation_ready": install["external_activation_ready"],
        },
        "external_execution_enabled": any(telecom["execution"].values()),
        "human_authority_final": True,
    }


@bp.get("/my-line")
@web_security.login_required()
def front_door():
    telecom = personal_telecom.status()
    response = make_response(
        render_template(
            "personal_telecom.html",
            telecom=telecom,
            surface=surface_status(),
            routes={item["id"]: item for item in FEATURE_ROUTES},
        )
    )
    return _no_store(response)


@bp.get("/my-line/status")
@web_security.login_required(api=True)
def status():
    return _no_store(make_response(jsonify(surface_status()), 200))


@bp.get("/my-line/passport")
@web_security.login_required(api=True)
def passport():
    telecom = personal_telecom.status()
    return _no_store(
        make_response(
            jsonify(
                network_passport=telecom["line"]["network_passport"],
                device_binding=telecom["line"]["device_binding"],
                oap_number=telecom["line"]["oap_number"],
                credential_material_exposed=False,
                hardware_identifiers_exposed=False,
            ),
            200,
        )
    )


@bp.get("/my-line/gates")
@web_security.login_required(api=True)
def gates():
    telecom = personal_telecom.status()
    return _no_store(
        make_response(
            jsonify(
                tracks=telecom["unlock_tracks"],
                remaining=telecom["remaining_gates"],
                execution=telecom["execution"],
                human_authority_final=True,
            ),
            200,
        )
    )


@bp.get("/my-line/install")
@web_security.login_required(api=True)
def install_status():
    return _no_store(make_response(jsonify(personal_telecom_install.status()), 200))


@bp.get("/my-line/recovery")
@web_security.login_required(api=True)
def recovery():
    telecom = personal_telecom.status()
    return _no_store(
        make_response(
            jsonify(
                oap_number=telecom["line"]["oap_number"],
                recovery_plan=telecom["recovery_plan"],
                preserves_oap_number=True,
                human_authority_final=True,
            ),
            200,
        )
    )


@bp.get("/my-line/routes")
@web_security.login_required(api=True)
def routes():
    return _no_store(
        make_response(
            jsonify(
                feature_routes=FEATURE_ROUTES,
                button_groups=BUTTON_GROUPS,
                mutation_routes_exposed=False,
            ),
            200,
        )
    )
