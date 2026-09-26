from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from mission_control import knowledge_core


class _Result:
    def __init__(self, *, one=None, all_rows=None):
        self._one = one
        self._all = all_rows or []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class _Connection:
    def __init__(self, identity, card_id):
        self.identity = identity
        self.card_id = card_id
        self.queries = []
        self.commits = 0

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        now = datetime(2026, 9, 26, tzinfo=timezone.utc)
        if "INSERT INTO oap_knowledge_cards" in sql:
            assert params[0] == self.identity
            return _Result(
                one=(
                    self.card_id,
                    params[1],
                    params[2],
                    params[3],
                    "RAW",
                    "PRIVATE",
                    now,
                    now,
                )
            )
        if "FROM oap_knowledge_cards" in sql and "SELECT card_id" in sql:
            assert params[0] == self.identity
            return _Result(
                all_rows=[
                    (
                        self.card_id,
                        "Private card",
                        "Owner scoped",
                        None,
                        "RAW",
                        "PRIVATE",
                        now,
                        now,
                    )
                ]
            )
        return _Result(one=(1,))

    def commit(self):
        self.commits += 1


def test_create_card_is_forced_private_and_records_history(monkeypatch):
    identity = str(uuid4())
    card_id = str(uuid4())
    connection = _Connection(identity, card_id)

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is False
        yield connection

    monkeypatch.setattr(knowledge_core.postgres_db, "connect", connect)

    card = knowledge_core.create_card(
        identity,
        title="Private card",
        insight="Owner scoped",
    )

    assert card["visibility"] == "PRIVATE"
    assert card["evidence_state"] == "RAW"
    assert connection.commits == 1
    sql = "\n".join(item[0] for item in connection.queries)
    assert "INSERT INTO oap_knowledge_history" in sql
    assert "PUBLIC" not in connection.queries[0][0]


def test_list_cards_always_filters_by_authenticated_owner(monkeypatch):
    identity = str(uuid4())
    card_id = str(uuid4())
    connection = _Connection(identity, card_id)

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield connection

    monkeypatch.setattr(knowledge_core.postgres_db, "connect", connect)

    cards = knowledge_core.list_cards(identity, query="Private")

    assert len(cards) == 1
    assert cards[0]["card_id"] == card_id
    query, params = connection.queries[0]
    assert "owner_identity_id=%s" in query
    assert params[0] == identity


def test_get_card_rejects_invalid_identity_before_database(monkeypatch):
    monkeypatch.setattr(
        knowledge_core.postgres_db,
        "connect",
        lambda **_kwargs: pytest.fail("database must not be reached"),
    )
    with pytest.raises(ValueError, match="invalid_identity"):
        knowledge_core.get_card("not-a-uuid", uuid4())
