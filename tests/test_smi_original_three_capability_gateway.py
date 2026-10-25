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


def test_m3gan_consent_denial_prevents_inventory_read(monkeypatch):
    monkeypatch.setattr(
        gateway.travel_marketplace, "public_offers",
        lambda **kwargs: pytest.fail("no read without consent"),
    )
    result = gateway.m3gan_consented_booking(
        {"request": "Find me a barber", "consent": False},
    )
    assert result["state"] == "blocked"
    assert result["data_read_performed"] is False
    assert result["reason"] == "explicit_consent_required"


def test_m3gan_rejects_unknown_or_ambiguous_request_without_fetch(monkeypatch):
    monkeypatch.setattr(
        gateway.travel_marketplace, "public_offers",
        lambda **kwargs: pytest.fail("ambiguous must not fetch"),
    )
    for query in ("find a barber or event", "what is the universe"):
        result = gateway.m3gan_consented_booking({"request": query, "consent": True})
        assert result["state"] == "needs_specific_category"


def test_m3gan_read_only_actual_offer_with_privacy_redaction(monkeypatch):
    monkeypatch.setattr(gateway.travel_supply_core, "SUPPLY_CATEGORIES", {"event", "barber"})
    calls = []

    def offers(**kwargs):
        calls.append(kwargs)
        return {
            "ready": True,
            "offers": [
                {
                    "category": "event", "certified_supplier": True,
                    "observed_not_inferred": True, "available_quantity": 3,
                    "listing_id": "listing-1", "title": "Real event",
                    "place_label": "Mitcham", "starts_at": "2026-11-01T12:00Z",
                    "ends_at": "2026-11-01T13:00Z", "unit_price_minor": 1000,
                    "currency": "GBP", "source": "oap_direct",
                    "supplier_name": "Certified organiser", "observed_at": "2026-10-25T20:00Z",
                    "buyer_identity_id": "private-buyer",
                    "api_secret": "must-not-leak",
                },
                {"category": "event", "certified_supplier": False,
                 "observed_not_inferred": True, "available_quantity": 9},
                {"category": "barber", "certified_supplier": True,
                 "observed_not_inferred": True, "available_quantity": 4},
            ],
        }

    monkeypatch.setattr(gateway.travel_marketplace, "public_offers", offers)
    result = gateway.m3gan_consented_booking(
        {"request": "Find concert tickets", "consent": True},
    )
    assert calls == [{"category": "event", "limit": 5}]
    assert result["state"] == "offers_found"
    assert result["count"] == 1
    assert result["booking_confirmed"] is False
    assert "buyer_identity_id" not in result["offers"][0]
    assert "api_secret" not in result["offers"][0]
    assert result["operation_performed"] is False


def test_m3gan_missing_barber_category_fails_closed(monkeypatch):
    monkeypatch.setattr(gateway.travel_supply_core, "SUPPLY_CATEGORIES", {"event"})
    monkeypatch.setattr(
        gateway.travel_marketplace, "public_offers",
        lambda **kwargs: pytest.fail("uninstalled category must not be queried"),
    )
    result = gateway.evaluate("m3gan", {"request": "Need a haircut", "consent": True})
    assert result["state"] == "not_ready"
    assert result["reason"] == "certified_category_not_installed"


def test_m3gan_empty_inventory_cannot_invent_availability(monkeypatch):
    monkeypatch.setattr(gateway.travel_supply_core, "SUPPLY_CATEGORIES", {"event"})
    monkeypatch.setattr(gateway.travel_marketplace, "public_offers",
                        lambda **kwargs: {"ready": True, "offers": []})
    result = gateway.evaluate("m3gan", {"request": "Any events?", "consent": True})
    assert result["state"] == "no_verified_offers"
    assert result["count"] == 0
    assert result["offers"] == []


def test_m3gan_unready_supply_does_not_claim_current_availability(monkeypatch):
    monkeypatch.setattr(gateway.travel_supply_core, "SUPPLY_CATEGORIES", {"event"})
    monkeypatch.setattr(gateway.travel_marketplace, "public_offers",
                        lambda **kwargs: {"ready": False, "error": "supply_core_not_ready"})
    result = gateway.evaluate("m3gan", {"request": "events today", "consent": True})
    assert result["state"] == "not_ready"
    assert result["reason"] == "supply_core_not_ready"


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
    with pytest.raises(ValueError, match="json_object_required"):
        gateway.evaluate("m3gan", "unexpected string")
    with pytest.raises(ValueError, match="unknown_original_three_profile"):
        gateway.evaluate("other", {})
