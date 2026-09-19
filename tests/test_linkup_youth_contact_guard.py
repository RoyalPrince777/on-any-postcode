from pathlib import Path


def test_youth_guard_stores_age_class_not_dob():
    source = Path("mission_control/link_youth_safety.py").read_text(encoding="utf-8")

    assert "link_age_classifications" in source
    assert "age_band" in source
    assert "minor" in source
    assert "adult" in source
    assert "date_of_birth" not in source
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
