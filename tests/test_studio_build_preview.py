import json
from uuid import uuid4

import pytest

from mission_control import studio_build_preview


def _files(label="One"):
    return {
        "index.html": f"<main><h1>{label}</h1><button id='demo'>Go</button></main>",
        "styles.css": "body{font-family:system-ui}",
        "app.js": "document.querySelector('#demo')?.addEventListener('click',()=>{});",
    }


def test_create_inspect_revise_and_readback(monkeypatch):
    owner = str(uuid4())
    store = []

    monkeypatch.setattr(
        studio_build_preview.workspaces,
        "list_studio_build_preview_records",
        lambda identity_id, preview_id, limit=100: list(store),
    )

    def save(identity_id, *, preview_id, version, digest, title, body):
        record_id = str(uuid4())
        store.append({
            "record_id": record_id,
            "title": title,
            "body": body,
            "status": "draft",
            "created_at": "2026-09-26T00:00:00+00:00",
            "updated_at": "2026-09-26T00:00:00+00:00",
        })
        return record_id

    monkeypatch.setattr(
        studio_build_preview.workspaces,
        "add_studio_build_preview_record_atomic",
        save,
    )

    created = studio_build_preview.create(owner, files=_files("One"), prompt="Build one")
    assert created["version"] == 1
    assert created["read_back_verified"] is True
    assert created["browser_isolated"] is True
    assert created["network_access_allowed"] is False
    assert created["production_deploy_authorised"] is False

    inspection = studio_build_preview.inspect(owner, created["preview_id"])
    assert inspection["counts"]["buttons"] == 1
    assert inspection["fix_loop_ready"] is True

    revised = studio_build_preview.revise(
        owner,
        created["preview_id"],
        files=_files("Two"),
        expected_last_hash=created["digest"],
    )
    assert revised["version"] == 2
    assert revised["digest"] != created["digest"]
    assert json.loads(store[1]["body"])["previous_hash"] == created["digest"]
    assert "Two" in studio_build_preview.render_document(owner, created["preview_id"])


def test_preview_rejects_active_html_network_and_server_risk():
    owner = str(uuid4())
    for bad in (
        "<script>alert(1)</script>",
        "<iframe src='x'></iframe>",
        "<form></form>",
        "<a href='https://example.com'>x</a>",
        "<img src='javascript:alert(1)'>",
    ):
        with pytest.raises(ValueError):
            studio_build_preview.create(
                owner,
                files={"index.html": bad, "styles.css": "", "app.js": ""},
            )


def test_stop_and_stale_revision_fail_closed(monkeypatch):
    owner = str(uuid4())
    with pytest.raises(PermissionError):
        studio_build_preview.create(owner, files=_files(), stopped=True)

    preview_id = str(uuid4())
    entry = studio_build_preview._entry(
        preview_id=preview_id,
        version=1,
        previous_hash="GENESIS",
        files=_files(),
        prompt_summary="",
    )
    monkeypatch.setattr(studio_build_preview, "_history", lambda *_: [entry])
    with pytest.raises(RuntimeError, match="stale_build_preview_version"):
        studio_build_preview.revise(
            owner,
            preview_id,
            files=_files("Two"),
            expected_last_hash="wrong",
        )


def test_status_truth_boundary():
    state = studio_build_preview.status()
    assert state["candidate_files_ready"] is True
    assert state["isolated_preview_ready"] is True
    assert state["inspect_ready"] is True
    assert state["revision_ready"] is True
    assert state["retest_ready"] is True
    assert state["production_deploy_authorised"] is False
    assert state["server_side_execution_authorised"] is False
