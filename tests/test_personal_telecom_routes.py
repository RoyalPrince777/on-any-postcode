from flask import Flask

from mission_control import personal_telecom_routes


def _app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(personal_telecom_routes.bp)
    return app


def test_my_line_routes_are_registered_read_only():
    rules = {
        rule.rule: set(rule.methods)
        for rule in _app().url_map.iter_rules()
        if rule.rule.startswith("/my-line")
    }

    expected = {
        "/my-line",
        "/my-line/status",
        "/my-line/passport",
        "/my-line/gates",
        "/my-line/install",
        "/my-line/recovery",
        "/my-line/routes",
    }
    assert expected <= set(rules)
    for route in expected:
        assert rules[route] == {"GET", "HEAD", "OPTIONS"}


def test_my_line_feature_catalog_has_unique_buttons_and_real_targets():
    features = personal_telecom_routes.FEATURE_ROUTES
    ids = [item["id"] for item in features]
    routes = [item["route"] for item in features]

    assert len(ids) == len(set(ids))
    assert len(routes) == len(set(routes))
    assert {
        "my_card",
        "link_up",
        "link_message",
        "link_call",
        "ptt",
        "passport",
        "gates",
        "install",
        "recovery",
        "status",
    } == set(ids)
    assert next(item for item in features if item["id"] == "link_call")["route"].startswith(
        "/linkup"
    )
    assert next(item for item in features if item["id"] == "link_message")["route"].startswith(
        "/linkup"
    )
    assert next(item for item in features if item["id"] == "ptt")["route"].startswith(
        "/linkup"
    )


def test_my_line_surface_reuses_existing_communications_instead_of_duplication(monkeypatch):
    monkeypatch.setattr(
        personal_telecom_routes.personal_telecom,
        "status",
        lambda: {
            "line": {
                "services": {
                    "link_call": "identity-ready",
                    "link_message": "identity-ready",
                    "ptt": "identity-ready",
                },
                "network_passport": {
                    "status": "registered",
                    "credential_material_exposed": False,
                },
            },
            "execution": {
                "real_carrier_profile_installed": False,
                "real_carrier_activation_enabled": False,
                "private_radio_transmission_enabled": False,
                "public_number_assigned": False,
                "sensitive_material_exposed": False,
            },
        },
    )
    monkeypatch.setattr(
        personal_telecom_routes.personal_telecom_install,
        "status",
        lambda: {
            "installer_built": True,
            "software_ready": True,
            "manifest_present": True,
            "external_activation_ready": False,
        },
    )

    surface = personal_telecom_routes.surface_status()

    assert surface["front_door"] == "/my-line"
    assert surface["button_count"] == 10
    assert surface["services"]["link_call"] == "identity-ready"
    assert surface["external_execution_enabled"] is False
    assert surface["human_authority_final"] is True


def test_button_groups_cover_every_feature_once():
    grouped = [
        button_id
        for group in personal_telecom_routes.BUTTON_GROUPS
        for button_id in group["buttons"]
    ]
    ids = [item["id"] for item in personal_telecom_routes.FEATURE_ROUTES]

    assert sorted(grouped) == sorted(ids)
    assert len(grouped) == len(set(grouped))


def test_my_line_front_door_has_all_primary_controls():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    template = (root / "mission_control" / "templates" / "personal_telecom.html").read_text(
        encoding="utf-8"
    )
    my_card = (root / "templates" / "my_card.html").read_text(encoding="utf-8")
    messenger = (root / "static" / "linkup_messenger.js").read_text(encoding="utf-8")
    linkup_template = (
        root / "mission_control" / "templates" / "linkup.html"
    ).read_text(encoding="utf-8")

    assert "My Line" in template
    assert "Network Passport" in template
    assert "Link Call" in template
    assert "Link Message" in template
    assert "PTT" in template
    assert 'href="/my-line"' in my_card
    assert "data-linkup-intent" in linkup_template
    assert 'intent === "link-call"' in messenger
    assert 'intent === "ptt"' in messenger
    assert 'intent === "message"' in messenger


def test_ptt_migration_is_explicit_and_bounded():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    migration = (root / "migrations" / "0011_link_voice_ptt_kind.sql").read_text(
        encoding="utf-8"
    )

    assert "ALTER TABLE link_voice_notes" in migration
    assert "ADD COLUMN IF NOT EXISTS kind" in migration
    assert "CHECK (kind IN ('voice','ptt'))" in migration
