from mission_control import infrastructure, personal_telecom


def test_personal_line_is_single_owner_and_single_primary_line():
    status = personal_telecom.status()

    assert status["validation"]["passed"] is True
    assert status["validation"]["single_owner"] is True
    assert status["validation"]["single_primary_line"] is True
    assert status["line"]["owner_scope"] == "self"


def test_personal_oap_number_is_first_party_namespace():
    status = personal_telecom.status()

    assert status["line"]["oap_number"] == "OAP-25-8-000001"
    assert status["line"]["oap_number"].startswith("OAP-")


def test_network_passport_exposes_no_credential_material():
    passport = personal_telecom.status()["line"]["network_passport"]

    assert passport["credential_material_exposed"] is False
    assert passport["carrier_profile_bound"] is False
    assert passport["production_esim_active"] is False


def test_device_binding_exposes_no_hardware_identifiers():
    binding = personal_telecom.status()["line"]["device_binding"]

    assert binding["mode"] == "single-primary-device"
    assert binding["hardware_identifiers_exposed"] is False
    assert binding["binding_status"] == "ready-for-owner-enrolment"


def test_personal_services_use_same_identity_anchor():
    services = personal_telecom.status()["line"]["services"]

    assert services == {
        "link_call": "identity-ready",
        "link_message": "identity-ready",
        "ptt": "identity-ready",
    }


def test_recovery_preserves_number_and_requires_revoke_before_rebind():
    recovery = personal_telecom.status()["line"]["recovery"]

    assert recovery["preserve_oap_number"] is True
    assert recovery["revoke_old_device_before_rebind"] is True
    assert recovery["human_authority_required"] is True


def test_real_carrier_public_number_and_radio_execution_remain_fail_closed():
    execution = personal_telecom.status()["execution"]

    assert all(value is False for value in execution.values())


def test_real_unlock_tracks_are_open_but_not_falsely_activated():
    status = personal_telecom.status()
    tracks = {track["id"]: track for track in status["unlock_tracks"]}

    assert set(tracks) == {
        "carrier_profile",
        "carrier_activation",
        "private_radio",
        "public_number",
    }
    assert all(track["state"] == "readiness-open" for track in tracks.values())
    assert all(track["software_owned"] is True for track in tracks.values())
    assert all(track["activation_proven"] is False for track in tracks.values())
    assert all(track["external_gate"] for track in tracks.values())
    assert all(track["evidence_required"] for track in tracks.values())


def test_personal_telecom_is_exposed_by_canonical_infrastructure_owner():
    projection = infrastructure.get_public_infrastructure()
    personal = projection["personal_telecom"]

    assert personal["system"] == "OAP Personal Telecom"
    assert personal["validation"]["passed"] is True
    assert "My Card -> My Line -> OAP Number" in personal["path"]
