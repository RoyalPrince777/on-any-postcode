from mission_control import bank_regulator_pack


def test_regulator_pack_has_digest_and_no_fake_signature(monkeypatch):
    register = {
        "legal_entity_and_ownership": {
            "proven": True,
            "status": "ACCEPTED",
            "evidence_reference": "company-proof",
            "reviewed_by": "founder",
            "recorded_at": "2026-10-02T00:00:00+00:00",
        }
    }

    def fake_register():
        return register

    monkeypatch.setattr(
        bank_regulator_pack.bank_authorisation_store,
        "latest_register",
        fake_register,
    )

    pack = bank_regulator_pack.build_pack()

    assert pack["pack_version"] == "oap_bank_regulator_pack_v1"
    assert pack["digest_algorithm"] == "SHA-256"
    assert len(pack["pack_digest"]) == 64
    assert pack["digital_signature_present"] is False
    assert pack["regulator_authorisation_granted"] is False
    assert pack["regulated_execution_enabled"] is False
    assert pack["evidence_accepted"] == 1
    assert bank_regulator_pack.verify_pack_digest(pack) is True


def test_regulator_pack_digest_detects_tampering(monkeypatch):
    monkeypatch.setattr(
        bank_regulator_pack.bank_authorisation_store,
        "latest_register",
        lambda: {},
    )
    pack = bank_regulator_pack.build_pack()
    assert bank_regulator_pack.verify_pack_digest(pack) is True

    tampered = dict(pack)
    tampered["authorised_bank"] = True
    assert bank_regulator_pack.verify_pack_digest(tampered) is False
