"""Real PostgreSQL proof for cross-worker SMI Studio Vision CPU admission.

Never tests a person's image or physical Android hardware. CI supplies
OAP_PRIMARY_DATABASE_URL and explicitly sets OAP_REAL_POSTGRES_PROOF=1.
"""
from __future__ import annotations

import base64
import os
from io import BytesIO

import pytest
from PIL import Image

from mission_control import postgres_db

PATH = "/mission/studio/vision/faces"
pytestmark = pytest.mark.skipif(
    os.getenv("OAP_REAL_POSTGRES_PROOF") != "1",
    reason="requires explicit real first-party PostgreSQL CI proof",
)


def _image_data():
    out = BytesIO()
    Image.new("RGB", (160, 120), (72, 103, 131)).save(out, format="PNG")
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def _send(client, csrf):
    return client.post(
        PATH,
        json={"image_data": _image_data()},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )


def test_postgres_shared_admission_blocks_other_database_connection(
    client, csrf, monkeypatch,
):
    """The production route must fail closed while another DB session owns lock."""
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setenv("RENDER", "true")
    with postgres_db.connect() as holder:
        assert holder.execute(
            "SELECT pg_try_advisory_xact_lock(%s, %s)", (777, 1305)
        ).fetchone() == (True,)
        blocked = _send(client, csrf)
        assert blocked.status_code == 503
        assert blocked.json["error"]["code"] == "face_detector_busy"
        assert blocked.headers["Cache-Control"] == "no-store"

    # The real transaction has now ended; a second connection can admit a
    # fresh request and the genuine offline detector may process a blank image.
    admitted = _send(client, csrf)
    assert admitted.status_code == 200
    assert admitted.json["identity_verified"] is False
    assert admitted.json["face_count"] == 0
    assert admitted.json["raw_content_retained"] is False
