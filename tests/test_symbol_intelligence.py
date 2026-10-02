from __future__ import annotations

import pytest

from oap.smi.symbol_intelligence import (
    SymbolIntelligenceBlocked,
    analyze,
    decode_symbol,
    status,
)


def running() -> bool:
    return False


def test_reel_decimal_values_are_unicode_not_occult_catalogue_numbers():
    result = analyze(
        (127748, "127774", "U+1F344", "🍇"),
        ("Every emoji is a sigil that can summon a demon and control you.",),
        stop_check=running,
    )
    assert [item["codepoint"] for item in result["symbols"]] == [
        "U+1F304",
        "U+1F31E",
        "U+1F344",
        "U+1F347",
    ]
    assert [item["unicode_name"] for item in result["symbols"]] == [
        "SUNRISE OVER MOUNTAINS",
        "SUN WITH FACE",
        "MUSHROOM",
        "GRAPES",
    ]
    claim = result["claims"][0]
    assert claim["classification"] == "EXTERNAL_EVIDENCE_REQUIRED"
    assert claim["verified_fact"] is False
    assert claim["human_review_required"] is True
    assert result["source_lookup_performed"] is False
    assert result["registry_write_performed"] is False
    assert result["receipt_persisted"] is False
    assert result["production_claim_allowed"] is False
    assert len(result["receipt_sha256"]) == 64


def test_receipt_is_deterministic_and_tamper_evident_for_same_input():
    first = analyze((127774,), ("Symbols affect attention.",), stop_check=running)
    second = analyze((127774,), ("Symbols affect attention.",), stop_check=running)
    changed = analyze((127775,), ("Symbols affect attention.",), stop_check=running)
    assert first["receipt_sha256"] == second["receipt_sha256"]
    assert first["receipt_sha256"] != changed["receipt_sha256"]


@pytest.mark.parametrize("token", (-1, 0x110000, 0xD800, "not-a-codepoint", True))
def test_invalid_unicode_fails_closed(token):
    with pytest.raises(SymbolIntelligenceBlocked):
        decode_symbol(token)


def test_stop_is_required_before_and_after_analysis():
    with pytest.raises(SymbolIntelligenceBlocked, match="stop_check_required"):
        analyze((127774,), stop_check=None)
    with pytest.raises(SymbolIntelligenceBlocked, match="stopped"):
        analyze((127774,), stop_check=lambda: True)

    observations = iter((False, True))
    with pytest.raises(SymbolIntelligenceBlocked, match="stopped"):
        analyze((127774,), stop_check=lambda: next(observations))


def test_status_does_not_claim_unbuilt_runtime_or_registry_integration():
    state = status()
    assert state["unicode_decode_ready"] is True
    assert state["bounded_claim_triage_ready"] is True
    assert state["image_ocr_ready"] is False
    assert state["video_transcription_ready"] is False
    assert state["authoritative_source_adapter_ready"] is False
    assert state["registry_persistence_ready"] is False
    assert state["runtime_wired"] is False
    assert state["production_ready"] is False
    assert state["human_authority_final"] is True
