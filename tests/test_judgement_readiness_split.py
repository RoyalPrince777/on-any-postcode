from __future__ import annotations

from contextlib import contextmanager

from mission_control import judgement, status


class Result:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


class Connection:
    def __init__(self, human_decisions: int):
        self.human_decisions = human_decisions

    def execute(self, sql, parameters=None):
        del parameters
        if "information_schema.tables" in sql:
            return Result(((1,),))
        if "COUNT(*) FILTER" in sql:
            return Result(((3, self.human_decisions),))
        raise AssertionError(sql)


def _connect_for(human_decisions: int):
    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield Connection(human_decisions)

    return connect


def test_judgement_engine_ready_without_fabricating_human_evidence(monkeypatch):
    monkeypatch.setattr(judgement.postgres_db, "connect", _connect_for(0))

    probe = judgement.status()

    assert probe["schema_ready"] is True
    assert probe["ready"] is True
    assert probe["reviews"] == 3
    assert probe["human_decisions"] == 0
    assert probe["human_evidence_ready"] is False


def test_human_evidence_becomes_ready_only_after_real_decision(monkeypatch):
    monkeypatch.setattr(judgement.postgres_db, "connect", _connect_for(1))

    probe = judgement.status()

    assert probe["ready"] is True
    assert probe["human_decisions"] == 1
    assert probe["human_evidence_ready"] is True


def test_public_projection_keeps_engine_and_approval_evidence_separate(monkeypatch):
    monkeypatch.setattr(
        status.judgement,
        "status",
        lambda: {
            "schema_ready": True,
            "automated_sections": 5,
            "total_sections": 6,
            "reviews": 3,
            "human_decisions": 0,
            "ready": True,
            "human_evidence_ready": False,
            "error": None,
        },
    )

    summary = status._postgres_approval_summary()

    assert summary["initialized"] is True
    assert summary["judgement_ready"] is True
    assert summary["evidence_ready"] is False
    assert "evidence pending" in summary["message"]
