from pathlib import Path


def test_youth_guard_stores_age_class_not_dob():
    source = Path("mission_control/link_youth_safety.py").read_text(encoding="utf-8")

    assert "link_age_classifications" in source
    assert "age_band" in source
    assert "minor" in source
    assert "adult" in source
    schema = source.split("SCHEMA_SQL =", 1)[1].split(
        "class LinkYouthSafetyUnavailable", 1
    )[0]
    assert "date_of_birth" not in schema
    assert '"stores_date_of_birth": False' in source
    assert '"unknown_is_guessed": False' in source


def test_youth_guard_requires_human_authority_for_classification():
    source = Path("mission_control/link_youth_safety.py").read_text(encoding="utf-8")

    assert "human_authority_approved is not True" in source
    assert "authority.require_human_authority" in source
    assert "verified_record" in source
    assert "human_authority" in source


def test_cross_age_policy_blocks_only_when_both_are_proven():
    source = Path("mission_control/link_youth_safety.py").read_text(encoding="utf-8")

    assert '"age_proof_unresolved"' in source
    assert '{"minor", "adult"}' in source
    assert '"youth_contact_restricted"' in source


def test_link_creation_paths_use_youth_guard():
    paths = {
        "mission_control/link_relationships.py": "request_link",
        "mission_control/product_store.py": "_link_guard",
        "mission_control/link_voice.py": "create_voice",
        "mission_control/link_share.py": "create_share",
        "mission_control/link_call_audit.py": "start_session",
        "mission_control/link_circles.py": "_guard_link",
        "mission_control/link_presence.py": "set_visibility",
    }
    for path, marker in paths.items():
        source = Path(path).read_text(encoding="utf-8")
        assert marker in source
        assert "link_youth_safety" in source
        assert "require_contact_allowed" in source


def test_historical_voice_and_share_reads_are_not_rewritten():
    voice = Path("mission_control/link_voice.py").read_text(encoding="utf-8")
    share = Path("mission_control/link_share.py").read_text(encoding="utf-8")

    assert "def list_voice" in voice
    assert "def read_voice" in voice
    assert "def list_shares" in share
    assert "def read_share" in share
    # The youth gate belongs on new contact actions, not evidence/history reads.
    assert voice.count("require_contact_allowed") == 1
    assert share.count("require_contact_allowed") == 1


def test_youth_guard_activation_is_explicit():
    source = Path("mission_control/__init__.py").read_text(encoding="utf-8")

    assert "OAP_LINK_YOUTH_GUARD_MIGRATION_ON_BOOT" in source
    assert "oap-link-youth-guard-status" in source
    assert "oap-init-link-youth-guard" in source


def test_youth_guard_failure_is_translated_by_link_subsystems():
    checks = {
        "mission_control/product_store.py": "link_youth_safety.LinkYouthSafetyUnavailable",
        "mission_control/link_relationships.py": "link_youth_guard_unavailable",
        "mission_control/link_voice.py": "voice_youth_guard_unavailable",
        "mission_control/link_share.py": "share_youth_guard_unavailable",
        "mission_control/link_call_audit.py": "link_call_youth_guard_unavailable",
        "mission_control/link_circles.py": "circle_youth_guard_unavailable",
        "mission_control/link_presence.py": "presence_youth_guard_unavailable",
    }
    for path, marker in checks.items():
        source = Path(path).read_text(encoding="utf-8")
        assert marker in source


def test_age_classification_has_explicit_authority_command():
    source = Path("mission_control/__init__.py").read_text(encoding="utf-8")

    assert 'oap-set-link-age-band' in source
    assert 'click.Choice(["minor", "adult"])' in source
    assert "human_authority_identity_not_configured" in source
    assert "human_authority_approved=True" in source


def test_linkup_safety_star_requires_youth_guard_readiness():
    source = Path("app.py").read_text(encoding="utf-8")

    assert 'linkup_safety.status().get("ready")' in source
    assert 'link_youth_safety.status().get("ready")' in source


def test_youth_policy_self_test_blocks_cross_age_without_real_identities():
    from mission_control import link_youth_safety

    proof = link_youth_safety.policy_self_test()

    assert proof == {
        "passed": True,
        "cross_age_blocked": True,
        "same_band_allowed": True,
        "unknown_unresolved": True,
        "uses_production_identities": False,
    }


def test_policy_from_bands_is_deterministic_and_privacy_minimised():
    from mission_control import link_youth_safety

    blocked = link_youth_safety.policy_from_bands("minor", "adult")
    allowed = link_youth_safety.policy_from_bands("adult", "adult")
    unknown = link_youth_safety.policy_from_bands(None, "adult")

    assert blocked["allowed"] is False
    assert blocked["reason"] == "youth_contact_restricted"
    assert allowed["allowed"] is True
    assert allowed["resolved"] is True
    assert unknown["allowed"] is True
    assert unknown["resolved"] is False


def test_youth_runtime_status_requires_self_test_pass():
    source = Path("mission_control/link_youth_safety.py").read_text(encoding="utf-8")

    assert 'result["policy_self_test"]["passed"] is True' in source
    assert "policy_from_bands(first_band, second_band)" in source


def test_youth_runtime_attestation_is_redacted():
    source = Path("mission_control/__init__.py").read_text(encoding="utf-8")

    assert "oap_link_youth_guard_runtime_proof" in source
    assert '"uses_production_identities": False' in source
    assert '"stores_date_of_birth": False' in source
    assert "policy_self_test_passed" in source
