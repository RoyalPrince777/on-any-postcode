"""Fail-closed station candidate selection: never confuse queue with delivered airplay."""
from contextlib import contextmanager
from uuid import uuid4

from mission_control import radio_core


def test_playout_candidate_is_scoped_to_active_approved_unstopped_station(monkeypatch):
    station, track, asset = (str(uuid4()) for _ in range(3))
    statements = []

    class Connection:
        def execute(self, sql, params):
            statements.append((sql, params))
            return self

        def fetchone(self):
            return (track, asset)

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield Connection()

    monkeypatch.setattr(radio_core.postgres_db, "connect", connect)
    result = radio_core.RadioStore().playout_candidate(station_id=station)
    sql, params = statements[0]
    assert params == (station,)
    for gate in (
        "s.founder_approved=TRUE",
        "s.state='ACTIVE'",
        "c.stopped=FALSE",
        "c.always_on=TRUE",
        "a.stopped=FALSE",
        "a.owner_identity_id=s.owner_identity_id",
        "r.owner_identity_id=s.owner_identity_id",
    ):
        assert gate in sql
    assert result["asset_id"] == asset
    assert result["track_id"] == track
    assert result["delivery_authorized"] is False
    assert result["station_stop_recheck_required"] is True
    assert result["airplay_receipt"] is None
    assert result["broadcast_started"] is False


def test_playout_candidate_denied_when_no_eligible_row(monkeypatch):
    station = str(uuid4())

    class Connection:
        def execute(self, _sql, _params):
            return self

        def fetchone(self):
            return None

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield Connection()

    monkeypatch.setattr(radio_core.postgres_db, "connect", connect)
    assert radio_core.RadioStore().playout_candidate(station_id=station) is None


def test_delivery_preflight_requires_exact_station_track_asset_and_stop(monkeypatch):
    station, track, asset = (str(uuid4()) for _ in range(3))
    statements = []
    selected = [None]

    class Connection:
        def execute(self, sql, params):
            statements.append((sql, params))
            return self

        def fetchone(self):
            return selected[0]

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield Connection()

    monkeypatch.setattr(radio_core.postgres_db, "connect", connect)
    store = radio_core.RadioStore()
    assert store.delivery_preflight(station_id=station, track_id=track, asset_id=asset) is False
    sql, params = statements[-1]
    assert params == (station, track, asset)
    for gate in (
        "r.track_id=%s",
        "a.asset_id=%s",
        "s.state='ACTIVE'",
        "s.founder_approved=TRUE",
        "c.stopped=FALSE",
        "c.always_on=TRUE",
        "a.stopped=FALSE",
        "a.owner_identity_id=s.owner_identity_id",
    ):
        assert gate in sql
    selected[0] = (1,)
    assert store.delivery_preflight(station_id=station, track_id=track, asset_id=asset) is True
