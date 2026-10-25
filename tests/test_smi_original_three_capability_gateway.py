"""Executable acceptance for the three bounded first-party film-inspired roles."""
import hashlib
import hmac
import json

import pytest

from mission_control import film_capability_gateway as gateway


def _signed_manifest(*, key="s" * 64, **changes):
    manifest = {
        "schema": gateway.MOTHERBOARD_SCHEMA,
        "component": "black_box",
        "workload_id": "readonly_001",
        "capabilities": ["inspect_public_evidence"],
        "network_access": False,
        "device_access": False,
        "writes_enabled": False,
        **changes,
    }
    data = json.dumps(manifest, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False).encode()
    return {
        "manifest": manifest,
        "signature": hmac.new(key.encode(), data, hashlib.sha256).hexdigest(),
    }


def test_all_three_roles_share_one_smi_and_cannot_execute():
    status = gateway.status()
    assert status["implemented_profiles"] == ("m3gan", "amelia", "black_box")
    assert status["one_smi_brain"] is True
    assert status["creates_agents"] is False
    assert status["independent_execution_authority"] is False
    assert status["physical_motherboard_built"] is False
    assert status["network_isolation_enforced_at_os_level"] is False
    assert status["live_film_character_equivalence"] is False
    assert status["other_business_missions_in_scope"] is False


def test_m3gan_consent_denial_prevents_film_source_read(monkeypatch):
    monkeypatch.setattr(
        gateway.smi_archive, "FILM_CANON_ABILITIES",
        None,
    )
    result = gateway.m3gan_consented_research(
        {"question": "What can M3GAN do?", "consent": False},
    )
    assert result["state"] == "blocked"
    assert result["source_access_performed"] is False
    assert result["reason"] == "explicit_consent_required"


def test_m3gan_original_film_abilities_are_sourced_and_identity_scoped():
    response = gateway.evaluate(
        "m3gan", {"question": "What can M3GAN do?", "consent": True},
    )
    assert response["state"] == "source_backed_matches"
    assert response["match_count"] == 6
    assert response["lookup_type"] == "deterministic_source_search_not_model_inference"
    assert response["autonomous_learning_performed"] is False
    assert response["external_fetch_performed"] is False
    assert response["question_stored"] is False
    assert response["context_stored"] is False
    assert response["operation_performed"] is False
    assert all(
        item["source_url"].startswith("https://")
        and item["publisher"]
        and item["source_id"]
        for item in response["matches"]
    )
    assert {item["ability_id"] for item in response["matches"]} == {
        "multi_sensor_perception", "adaptive_social_learning",
        "unsupervised_goal_selection", "digital_survival",
        "upgraded_android_combat", "connected_body_control",
    }


def test_m3gan_relevance_uses_bounded_user_supplied_context():
    result = gateway.evaluate(
        "m3gan",
        {"question": "Tell me more", "context": ["digital survival"], "consent": True},
    )
    assert result["state"] == "source_backed_matches"
    assert any(i["ability_id"] == "digital_survival" for i in result["matches"])
    assert result["context_stored"] is False


def test_m3gan_out_of_scope_terms_have_no_invented_film_facts():
    result = gateway.evaluate(
        "m3gan", {"question": "quantum graviton hyperdrive", "consent": True},
    )
    assert result["state"] == "no_verified_match"
    assert result["matches"] == []


def test_m3gan_rejects_unbounded_or_private_history():
    for bad_context in (
        ["a"] * 4,
        ["a" * 121],
        "someone's entire private messages",
        [1],
    ):
        with pytest.raises((ValueError, TypeError)):
            gateway.evaluate(
                "m3gan",
                {"question": "digital survival", "context": bad_context, "consent": True},
            )


def test_m3gan_response_excludes_business_and_other_mission_data():
    response = gateway.evaluate(
        "m3gan", {"question": "original abilities", "consent": True},
    )
    assert response["source"] == "oap_founder_private_film_canon_snapshot"
    assert response["physical_action_performed"] is False
    assert "offers" not in response
    assert "booking_confirmed" not in response
    assert "area" not in response


def test_amelia_prevents_powerful_actions_even_with_self_declared_evidence():
    for action in ("deploy", "secret_export", "infiltration", "self_modify",
                   "public_precise_tracking", "remote_code_execution"):
        result = gateway.evaluate(
            "amelia", {"action": action, "source_verified": True},
        )
        assert result["decision"] == "hold"
        assert result["action_executed"] is False
        assert result["guardian_required"] is True


def test_amelia_unknown_or_unverified_actions_fail_closed():
    for action, verified in (
        ("new_undocumented_tool", True),
        ("inspect_public_evidence", False),
    ):
        result = gateway.evaluate(
            "amelia", {"action": action, "source_verified": verified},
        )
        assert result["decision"] == "hold"
        assert result["operation_performed"] is False


def test_amelia_only_recommends_review_of_known_evidenced_read():
    result = gateway.evaluate(
        "amelia", {"action": "inspect_public_evidence", "source_verified": True},
    )
    assert result["decision"] == "review_only"
    assert result["action_executed"] is False
    assert result["shere_khan_review_preserved"] is True
    assert result["bagheera_review_preserved"] is True


def test_black_box_actual_hmac_sha256_verification_is_software_only():
    payload = _signed_manifest()
    accepted = gateway.verify_black_box_manifest(payload, secret="s" * 64)
    assert accepted["integrity_verified"] is True
    assert accepted["admitted_read_only"] is True
    assert accepted["state"] == "admitted_read_only"
    assert accepted["manifest_sha256"]
    assert accepted["network_used"] is False
    assert accepted["device_used"] is False
    assert accepted["hardware_attestation"] is False
    assert accepted["sandbox_process_started"] is False


def test_black_box_unsigned_tampered_and_weak_keys_all_fail_closed():
    payload = _signed_manifest()
    forged = dict(payload)
    forged["signature"] = "0" * 64
    assert gateway.verify_black_box_manifest(forged, secret="s" * 64)["state"] == "blocked"
    assert gateway.verify_black_box_manifest(payload, secret="short")["state"] == "blocked"
    altered = dict(payload)
    altered["manifest"] = dict(payload["manifest"], workload_id="changed_workload_999")
    assert gateway.verify_black_box_manifest(altered, secret="s" * 64)["state"] == "blocked"


def test_black_box_privileged_or_network_manifest_denied_even_if_signed():
    for change in (
        {"network_access": True},
        {"device_access": True},
        {"writes_enabled": True},
        {"capabilities": ["deploy"]},
        {"capabilities": ["inspect_public_evidence", "inspect_public_evidence"]},
        {"admin_override": True},
    ):
        result = gateway.verify_black_box_manifest(
            _signed_manifest(**change), secret="s" * 64,
        )
        assert result["state"] == "blocked"
        assert result["admitted_read_only"] is False


def test_black_box_requires_real_configured_server_key(monkeypatch):
    monkeypatch.delenv(gateway.MOTHERBOARD_KEY_ENV, raising=False)
    payload = _signed_manifest()
    result = gateway.evaluate("black_box", payload)
    assert result["reason"] == "signing_key_unconfigured"
    assert result["integrity_verified"] is False
    assert result["admitted_read_only"] is False


def test_gateway_rejects_non_json_and_unknown_profile():
    with pytest.raises(TypeError, match="json_object_required"):
        gateway.evaluate("m3gan", "unexpected string")
    with pytest.raises(ValueError, match="unknown_original_three_profile"):
        gateway.evaluate("other", {})
