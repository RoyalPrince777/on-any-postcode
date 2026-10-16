"""Regression coverage for Nirmata's advisory research contract."""
import pytest

from mission_control.nirmata_research import (
    ANATOMY_LENSES,
    research_blueprint,
    verify_blueprint_integrity,
)


def _blueprint(**changes):
    args = {"question": "How can recovery improve?", "domain": "software",
            "sources": {"paper-1": "Author, study, 2025"},
            "hypotheses": ["Recovery time decreases with redundancy"],
            "lenses": ["structure", "repair"]}
    args.update(changes)
    return research_blueprint(**args)


def test_blueprint_is_deterministic_and_never_grants_authority():
    first = _blueprint()
    assert first == _blueprint()
    assert len(first["provenance_sha256"]) == 64
    assert first["evidence_status"] == "unverified_references"
    assert first["verification_required"] is True
    assert first["execution_authorised"] is False
    assert first["medical_diagnosis_authorised"] is False
    assert first["identity_issuance_authorised"] is False


def test_missing_sources_fail_closed_on_evidence():
    result = _blueprint(sources={})
    assert result["evidence_status"] == "missing"
    assert result["verification_required"] is True


@pytest.mark.parametrize("changes", [
    {"question": ""},
    {"domain": ""},
    {"sources": {"id": ""}},
    {"sources": {"id": 42}},
    {"hypotheses": [""]},
    {"lenses": ["unknown"]},
    {"lenses": ["repair", "repair"]},
    {"lenses": [1]},
])
def test_invalid_blueprints_are_rejected(changes):
    with pytest.raises(ValueError):
        _blueprint(**changes)


def test_all_research_lenses_are_unique():
    assert len(ANATOMY_LENSES) == 21
    assert len(set(ANATOMY_LENSES)) == 21


def test_blueprint_integrity_rejects_tampering():
    record = _blueprint()
    assert verify_blueprint_integrity(record)
    assert not verify_blueprint_integrity({**record, "question": "altered"})
    assert not verify_blueprint_integrity({**record, "execution_authorised": True})
    assert not verify_blueprint_integrity({**record, "provenance_sha256": "invalid"})
