from pathlib import Path

from mission_control import public_store

ROOT = Path(__file__).resolve().parents[1]


def test_signal_roundtrip_probe_is_residue_free_and_uses_signal_scope():
    text = (ROOT / "mission_control" / "public_store.py").read_text()

    assert "oap-signal-probe-" in text
    assert "PUBLIC_SIGNAL_SCOPE" in text
    assert "connection.rollback()" in text
    assert "decoded == expected" in text
    assert "EXISTS(SELECT 1 FROM users WHERE id=%s)" in text
    assert "EXISTS(SELECT 1 FROM posts WHERE id=%s)" in text


def test_signal_payload_decoder_matches_public_feed_shape():
    raw = '{"name":"OAP Probe","body":"useful local signal"}'

    assert public_store._decode_object(raw) == {
        "name": "OAP Probe",
        "body": "useful local signal",
    }


def test_render_durability_requires_signal_roundtrip():
    text = (ROOT / "mission_control" / "public_store.py").read_text()

    assert 'os.environ.get("RENDER", "").lower() == "true"' in text
    assert 'result["signal_roundtrip_ready"] = _signal_roundtrip_probe()' in text
    assert 'result["schema_ready"] and result["signal_roundtrip_ready"]' in text
