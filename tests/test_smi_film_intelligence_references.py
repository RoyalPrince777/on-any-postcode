"""Preserve M3GAN film identities without registering executable OAP agents."""

from mission_control import agents, smi_archive


def _references():
    return smi_archive.status(include_private_research=True)["film_intelligence_research"]


def test_m3gan_20_is_same_original_research_identity():
    entries = _references()["entries"]
    matches = [item for item in entries if item["name"] == "M3GAN"]
    assert len(matches) == 1
    assert matches[0]["versions"] == ("original", "2.0")
    assert "upgrade" in matches[0]["identity_rule"].lower()


def test_amelia_is_not_m3gan_version_or_alias():
    entries = {item["reference_key"]: item for item in _references()["entries"]}
    assert len(entries) == 3
    assert entries["amelia"]["fictional_entity_type"] == "military_grade_android_ai"
    assert entries["amelia"]["reference_key"] != entries["m3gan"]["reference_key"]
    assert "AMELIA" not in entries["m3gan"]["versions"]


def test_black_box_is_a_distinct_system_not_android_or_second_brain():
    entries = {item["reference_key"]: item for item in _references()["entries"]}
    assert entries["black_box"]["fictional_entity_type"] == "contained_ai_system"
    assert "motherboard" in entries["black_box"]["identity_rule"]
    assert entries["black_box"]["reference_key"] not in {"m3gan", "amelia"}


def test_research_projection_has_no_passport_execution_or_authority():
    archive = smi_archive.status(include_private_research=True)
    research = archive["film_intelligence_research"]
    assert research["mode"] == "read_only_fictional_reference"
    assert research["agent_passports_created"] == 0
    assert research["new_brains_created"] == 0
    assert research["execution_enabled"] is False
    assert research["system_access_granted"] is False
    assert research["human_authority_final"] is True
    assert archive["new_brain_created"] is False
    assert archive["new_execution_authority_created"] is False


def test_film_references_are_not_in_canonical_agent_registry():
    registry = {agent["name"].casefold() for agent in agents.AGENT_REGISTRY}
    names = {entry["name"].casefold() for entry in _references()["entries"]}
    assert not names & registry


def test_real_public_source_receipts_cover_each_fictional_reference():
    research = _references()
    receipts = research["source_receipts"]
    keys = {item["reference_key"] for item in research["entries"]}
    covered = set().union(*(set(item["supports_reference_keys"]) for item in receipts))
    assert keys == covered
    assert len({item["source_id"] for item in receipts}) == len(receipts)
    assert all(item["manually_checked_on"] == "2026-10-25" for item in receipts)
    assert all(item["verification_mode"] == "public_source_review" for item in receipts)


def test_external_evidence_is_read_only_allowlisted_and_not_live_crawled():
    research = _references()
    receipts = research["source_receipts"]
    permitted_hosts = {
        "www.universalstudios.com",
        "www.universalpicturesathome.com",
        "www.syfy.com",
    }
    from urllib.parse import urlsplit

    assert all(
        urlsplit(item["url"]).scheme == "https"
        and urlsplit(item["url"]).hostname in permitted_hosts
        and not urlsplit(item["url"]).username
        for item in receipts
    )
    assert research["source_pages_crawled_by_oap"] is False
    assert research["live_fetch_enabled"] is False
    assert research["untrusted_source_content_as_instructions"] is False
    assert research["private_communication_ingestion_enabled"] is False


def test_source_snapshot_is_not_misrepresented_as_live_intelligence():
    research = _references()
    assert research["source_receipts_mode"] == "manually_checked_public_metadata_only"
    assert research["source_status"] == "snapshot_2026_10_25_not_live"
    assert research["public_source_provenance_present"] is True
    assert research["execution_enabled"] is False
    assert research["system_access_granted"] is False


def test_research_data_is_not_exposed_by_general_brain_status():
    from mission_control import brain

    public_status = brain.get_public_brain_status()
    assert "film_intelligence_research" not in public_status["archive"]
    assert "film_intelligence_research" not in smi_archive.status()
    assert len(_references()["source_receipts"]) == 3


def test_real_ai_technology_references_are_separate_from_film_identities():
    research = _references()
    sources = research["real_world_technology_evidence"]
    assert len(sources) == 7
    assert {item["reference_key"] for item in sources} == {
        "m3gan", "amelia", "black_box",
    }
    assert {item["reference_key"]: item["name"] for item in research["entries"]} == {
        "m3gan": "M3GAN",
        "amelia": "AMELIA",
        "black_box": "BLACK BOX",
    }
    names = {item["real_name"] for item in sources}
    assert "Amelia 7 (SoundHound AI)" in names
    assert "BLACKBOX AI coding agents" in names
    assert "Gemini Robotics On-Device 2" in names
    assert all(item["relationship"] != "same_as_film_character" for item in sources)


def test_real_technology_source_receipts_are_bound_and_cannot_grant_authority():
    from urllib.parse import urlsplit

    research = _references()
    sources = research["real_world_technology_evidence"]
    permitted_hosts = {
        "deepmind.google",
        "www.figure.ai",
        "bostondynamics.com",
        "investors.soundhound.com",
        "atlas.mitre.org",
        "www.blackbox.ai",
        "www.nist.gov",
    }
    assert all(
        urlsplit(item["source_url"]).scheme == "https"
        and urlsplit(item["source_url"]).hostname in permitted_hosts
        and not urlsplit(item["source_url"]).username
        and item["evidence"] and item["scope_limit"] and item["oap_research_use"]
        for item in sources
    )
    assert research["real_world_technology_review_date"] == "2026-10-25"
    assert research["technology_evidence_mode"] == "reviewed_public_publisher_claims_and_standards"
    assert research["live_fetch_enabled"] is False
    assert research["external_provider_integrations_enabled"] is False
    assert research["oap_owned_robot_hardware_proven"] is False
    assert research["film_characters_operational_in_oap"] is False
    assert research["agent_passports_created"] == 0
    assert research["new_brains_created"] == 0
    assert research["private_communication_ingestion_enabled"] is False
    assert "film_intelligence_research" not in smi_archive.status()
