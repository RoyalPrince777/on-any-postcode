"""Real PostgreSQL proof for cross-worker SMI Studio Vision CPU admission.

Never tests a person's image or physical Android hardware. CI supplies
OAP_PRIMARY_DATABASE_URL and explicitly sets OAP_REAL_POSTGRES_PROOF=1.
"""
from __future__ import annotations

import base64
import multiprocessing
import os
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from PIL import Image

from mission_control import postgres_db, studio_face_admission

PATH = "/mission/studio/vision/faces"
pytestmark = pytest.mark.skipif(
    os.getenv("OAP_REAL_POSTGRES_PROOF") != "1",
    reason="requires explicit real first-party PostgreSQL CI proof",
)
AUTH_ID = "11111111-1111-4111-8111-111111111111"
QUOTA_ID = "22222222-2222-4222-8222-222222222222"


@pytest.fixture(autouse=True)
def isolated_quota_schema():
    # Never migrate or clear an operational database from a test invocation.
    assert urlsplit(os.environ["OAP_PRIMARY_DATABASE_URL"]).hostname in {
        "127.0.0.1", "localhost", "::1",
    }
    sql = (Path(__file__).resolve().parents[1] /
           "migrations/0014_studio_vision_quota.sql").read_text()
    with postgres_db.connect() as connection:
        connection.execute(sql)
        connection.execute(
            "DELETE FROM oap_studio_vision_quota WHERE identity_id IN (%s, %s)",
            (AUTH_ID, QUOTA_ID),
        )
    yield
    with postgres_db.connect() as connection:
        connection.execute(
            "DELETE FROM oap_studio_vision_quota WHERE identity_id IN (%s, %s)",
            (AUTH_ID, QUOTA_ID),
        )


def _quota_process(results):
    results.put(studio_face_admission.reserve_shared_quota(QUOTA_ID))


def _application_process(results, entered=None, release=None):
    """Independent Flask WSGI process with fixture auth, not deployed HTTPS."""
    import app as app_module
    from mission_control import neon_auth, studio_face_detection, web_security

    os.environ.update(
        OAP_SMI_FACE_DETECTION_ENABLED="true", OAP_SMI_FACE_SHARED_GUARD_REQUIRED="true",
        OAP_HUMAN_AUTHORITY_EMAIL="member@example.test",
        NEON_AUTH_BASE_URL="https://example.neonauth.test/neondb/auth",
    )
    neon_auth.get_session = lambda _: neon_auth.AuthResult(
        status_code=200, payload={"session": {"id": "isolated-worker"},
                                  "user": {"id": AUTH_ID, "email": "member@example.test",
                                           "emailVerified": True}},
    )
    app_module.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    if entered is not None:
        original = studio_face_detection.detect_faces_bounded

        def held(image):
            entered.set()
            assert release.wait(15), "parent did not release controlled detector"
            return original(image)

        studio_face_detection.detect_faces_bounded = held
    with app_module.app.test_client() as worker:
        worker.set_cookie("better-auth.session_token", "isolated-worker-session")
        with worker.session_transaction() as session:
            session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = ["better-auth.session_token"]
            session[web_security.CSRF_SESSION_KEY] = "isolated-worker-csrf-token-1234567890"
        response = _send(worker, {"csrf_token": "isolated-worker-csrf-token-1234567890"})
        results.put((response.status_code, response.json))


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


def test_quota_is_atomic_across_independent_processes_and_restart():
    context = multiprocessing.get_context("spawn")
    results = context.Queue()
    workers = [context.Process(target=_quota_process, args=(results,)) for _ in range(9)]
    try:
        for worker in workers:
            worker.start()
        admissions = [results.get(timeout=20) for _ in workers]
        assert admissions.count(True) == 7
        assert admissions.count(False) == 2
        for worker in workers:
            worker.join(timeout=5)
            assert worker.exitcode == 0
        restarted = context.Process(target=_quota_process, args=(results,))
        workers.append(restarted)
        restarted.start()
        assert results.get(timeout=15) is False
        restarted.join(timeout=5)
        assert restarted.exitcode == 0
        with postgres_db.connect() as connection:
            row = connection.execute(
                "SELECT cardinality(attempts) FROM oap_studio_vision_quota WHERE identity_id=%s",
                (QUOTA_ID,),
            ).fetchone()
            assert row == (7,)
            connection.execute(
                """UPDATE oap_studio_vision_quota
                   SET attempts=ARRAY[statement_timestamp() - INTERVAL '61 seconds']
                   WHERE identity_id=%s""", (QUOTA_ID,),
            )
        assert studio_face_admission.reserve_shared_quota(QUOTA_ID) is True
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.kill()
            worker.join(timeout=5)
        results.close()


def test_two_application_processes_reject_overlap_then_recover():
    context = multiprocessing.get_context("spawn")
    results = context.Queue()
    entered, release = context.Event(), context.Event()
    first = context.Process(target=_application_process, args=(results, entered, release))
    second = context.Process(target=_application_process, args=(results,))
    third = context.Process(target=_application_process, args=(results,))
    workers = [first, second, third]
    try:
        first.start()
        assert entered.wait(15), "first application did not reach shared admission"
        second.start()
        status, payload = results.get(timeout=15)
        assert status == 503
        assert payload["error"]["code"] == "face_detector_busy"
        second.join(timeout=5)
        assert second.exitcode == 0
        release.set()
        assert results.get(timeout=15)[0] == 200
        first.join(timeout=5)
        assert first.exitcode == 0
        third.start()
        assert results.get(timeout=15)[0] == 200
        third.join(timeout=5)
        assert third.exitcode == 0
    finally:
        release.set()
        for worker in workers:
            if worker.pid is not None:
                if worker.is_alive():
                    worker.kill()
                worker.join(timeout=5)
        results.close()
