import json
import uuid

import pytest

from mission_control import reviews


class _Row:
    pass


def test_review_validates_rating_and_identity():
    with pytest.raises(ValueError, match="invalid_review_rating"):
        reviews._rating(0)
    with pytest.raises(ValueError, match="invalid_review_rating"):
        reviews._rating(6)
    assert reviews._rating("5") == 5
    assert reviews._identity(str(uuid.uuid4()))


def test_review_list_parses_first_party_workspace_rows(monkeypatch):
    product_id = str(uuid.uuid4())
    record_id = str(uuid.uuid4())
    identity_id = str(uuid.uuid4())

    class Conn:
        def execute(self, sql, params):
            class Result:
                def fetchall(self_inner):
                    return [(
                        uuid.UUID(record_id),
                        uuid.UUID(identity_id),
                        json.dumps({"product_id": product_id, "rating": 5, "body": "Excellent"}),
                        __import__("datetime").datetime.datetime(2026, 9, 26, 16, 0),
                        "Tester",
                    )]
            return Result()

    class Ctx:
        def __enter__(self): return Conn()
        def __exit__(self, *args): return False

    monkeypatch.setattr(reviews.postgres_db, "connect", lambda readonly=True: Ctx())

    rows = reviews.list_reviews(product_id)
    assert rows[0]["rating"] == 5
    assert rows[0]["body"] == "Excellent"
    assert rows[0]["first_party"] is True
    assert rows[0]["owner_scoped_write"] is True


def test_review_status_reuses_existing_schema_without_migration(monkeypatch):
    class Conn:
        def execute(self, sql):
            class Result:
                def fetchall(self_inner):
                    return [("oap_workspace_records",), ("products",), ("users",)]
            return Result()

    class Ctx:
        def __enter__(self): return Conn()
        def __exit__(self, *args): return False

    monkeypatch.setattr(reviews.postgres_db, "connect", lambda readonly=True: Ctx())
    state = reviews.status()
    assert state["ready"] is True
    assert state["schema_migration_required"] is False
    assert state["external_review_authority"] is False
