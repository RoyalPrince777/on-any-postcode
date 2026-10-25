"""Preserve M3GAN film identities without registering executable OAP agents."""

from mission_control import agents, smi_archive


def _references():
    return smi_archive.status()["film_intelligence_research"]


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
    archive = smi_archive.status()
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


def test_evidence_is_wired_to_existing_brain_archive_projection():
    from mission_control import brain

    status = brain.get_public_brain_status()
    research = status["archive"]["film_intelligence_research"]
    assert len(research["source_receipts"]) == 3
    assert {item["reference_key"] for item in research["entries"]} == {
        "m3gan", "amelia", "black_box",
    }
    assert research["private_communication_ingestion_enabled"] is False
