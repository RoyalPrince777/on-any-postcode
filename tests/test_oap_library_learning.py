from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mission_control import oap_library_learning, oap_library_views

ROOT = Path(__file__).resolve().parents[1]


class _Result:
    def __init__(self, *, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []
        self.committed = False

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split())
        self.calls.append((normalized, params))
        return self.handler(normalized, params)

    def commit(self):
        self.committed = True


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def test_learning_schema_is_explicit_private_and_bounded():
    dry_run = oap_library_learning.init_schema(dry_run=True)
    joined = "\n".join(dry_run["statements"])

    assert dry_run["version"] == "oap_library_learning_v1"
    assert dry_run["applied"] is False
    assert "oap_library_learning_records" in joined
    assert "visibility = 'PRIVATE'" in joined
    assert "rights_attested IS TRUE" in joined
    assert "identity_id UUID NOT NULL REFERENCES users(id)" in joined
    assert oap_library_learning.MAX_REFLECTION_CHARS == 600
    assert oap_library_learning.MAX_RECORDS_PER_MEMBER == 100

    with pytest.raises(PermissionError, match="explicit_confirmation_required"):
        oap_library_learning.init_schema()


def test_learning_schema_has_governed_public_service_activation():
    init_source = (ROOT / "mission_control" / "__init__.py").read_text()
    blueprint = (ROOT / "render.yaml").read_text()

    assert 'OAP_LIBRARY_LEARNING_MIGRATION_ON_BOOT", "").strip() == "1"' in init_source
    assert "oap_library_learning.init_schema(assume_yes=True)" in init_source
    public_service = blueprint.split("name: on-any-postcode", 1)[1].split(
        "name: oap-routing", 1
    )[0]
    private_gateway = blueprint.split("name: oap-smi", 1)[1].split(
        "name: on-any-postcode", 1
    )[0]
    assert "OAP_LIBRARY_LEARNING_MIGRATION_ON_BOOT" in public_service
    assert "OAP_LIBRARY_LEARNING_MIGRATION_ON_BOOT" not in private_gateway


def test_learning_record_is_catalogue_bound_and_requires_member_rights():
    record = oap_library_learning.prepare_record(
        food_id="carrot",
        area_id="eyes",
        reflection="I learned why sources must stay attached.",
        rights_attested=True,
    )

    assert record["book_id"] == "food-book"
    assert record["food_id"] == "carrot"
    assert record["visibility"] == "PRIVATE"
    assert record["rights_basis"] == oap_library_learning.RIGHTS_BASIS
    assert record["content_hash"]
    assert [source["id"] for source in record["sources"]] == ["nih-vitamin-a"]

    with pytest.raises(PermissionError, match="rights_attestation_required"):
        oap_library_learning.prepare_record(
            food_id="carrot",
            area_id="eyes",
            reflection="Mine",
            rights_attested=False,
        )
    with pytest.raises(ValueError, match="food_area_pair_required"):
        oap_library_learning.prepare_record(
            food_id="carrot",
            area_id="gut",
            reflection="Mine",
            rights_attested=True,
        )
    with pytest.raises(ValueError, match="reflection_too_long"):
        oap_library_learning.prepare_record(
            food_id="carrot",
            area_id="eyes",
            reflection="x" * 601,
            rights_attested=True,
        )


def test_create_learning_record_writes_private_integrity_snapshot(monkeypatch):
    identity = str(uuid.uuid4())
    record_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    def handler(query, params):
        if query.startswith("INSERT INTO users"):
            assert params[0] == identity
            assert params[1].startswith("oap-library-")
            return _Result()
        if query.startswith("SELECT COUNT(*)"):
            return _Result(row=(0,))
        if query.startswith("INSERT INTO oap_library_learning_records"):
            assert params[0] == identity
            assert params[1:4] == ("food-book", "carrot", "eyes")
            assert json.loads(params[6])[0]["id"] == "nih-vitamin-a"
            assert params[7] == oap_library_learning.RIGHTS_BASIS
            assert params[8] == "PRIVATE"
            assert len(params[9]) == 64
            return _Result(row=(record_id, created_at))
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(
        oap_library_learning.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    result = oap_library_learning.create_record(
        identity,
        food_id="carrot",
        area_id="eyes",
        reflection="My source-backed learning.",
        rights_attested=True,
        display_name="Member",
    )

    assert connection.committed is True
    assert result["record_id"] == record_id
    assert result["visibility"] == "PRIVATE"
    assert "OFFICIAL SOURCES" in result["export_text"]
    assert "My source-backed learning." in result["export_text"]


def test_list_learning_records_rejects_integrity_drift(monkeypatch):
    identity = str(uuid.uuid4())
    prepared = oap_library_learning.prepare_record(
        food_id="carrot",
        area_id="eyes",
        reflection="Original reflection",
        rights_attested=True,
    )
    row = (
        str(uuid.uuid4()),
        prepared["book_id"],
        prepared["food_id"],
        prepared["area_id"],
        prepared["fact"],
        "Changed after hashing",
        json.dumps(prepared["sources"]),
        prepared["rights_basis"],
        True,
        prepared["visibility"],
        prepared["content_hash"],
        datetime.now(timezone.utc),
    )
    connection = _Connection(lambda _query, _params: _Result(rows=[row]))
    monkeypatch.setattr(
        oap_library_learning.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    with pytest.raises(
        oap_library_learning.LibraryLearningUnavailable,
        match="learning_record_integrity_failed",
    ):
        oap_library_learning.list_records(identity)


def test_food_book_page_contains_real_learning_create_preserve_share_controls(client):
    body = client.get("/library/food-book").get_data(as_text=True)

    assert "Start with the evidence" in body
    assert "Check your understanding" in body
    assert "Build learning card" in body
    assert "Preserve privately" in body
    assert "Share from device" in body
    assert "Nothing has been shared" not in body
    assert 'data-learning-records-url="/library/food-book/learning-records"' in body
    assert "NHS · B vitamins and folic acid" in body
    assert "NHS · Vitamin C" in body


def test_learning_record_api_requires_csrf_and_keeps_member_scope(
    client, csrf, monkeypatch
):
    record = {
        "record_id": str(uuid.uuid4()),
        "book_id": "food-book",
        "food_id": "carrot",
        "area_id": "eyes",
        "fact": "Carrot fact",
        "reflection": "My reflection",
        "sources": [],
        "rights_basis": oap_library_learning.RIGHTS_BASIS,
        "rights_attested": True,
        "visibility": "PRIVATE",
        "content_hash": "a" * 64,
        "created_at": "2026-09-22T18:00:00+00:00",
        "export_text": "OAP Food Book",
    }
    captured = {}

    def create(identity, **values):
        captured["identity"] = identity
        captured.update(values)
        return record

    monkeypatch.setattr(oap_library_views.oap_library_learning, "create_record", create)
    monkeypatch.setattr(
        oap_library_views.oap_library_learning,
        "list_records",
        lambda identity: [record] if identity else [],
    )

    denied = client.post(
        "/library/food-book/learning-records",
        json={
            "food_id": "carrot",
            "area_id": "eyes",
            "reflection": "Mine",
            "rights_attested": True,
        },
    )
    assert denied.status_code == 403
    assert denied.get_json()["error"]["code"] == "csrf_failed"

    response = client.post(
        "/library/food-book/learning-records",
        json={
            "food_id": "carrot",
            "area_id": "eyes",
            "reflection": "Mine",
            "rights_attested": True,
        },
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 201
    assert response.get_json()["record"]["visibility"] == "PRIVATE"
    assert captured["food_id"] == "carrot"
    assert captured["rights_attested"] is True

    listed = client.get("/library/food-book/learning-records")
    assert listed.status_code == 200
    assert listed.get_json()["records"][0]["record_id"] == record["record_id"]


def test_learning_record_api_is_not_public(anonymous_client):
    response = anonymous_client.get(
        "/library/food-book/learning-records",
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"
