"""No-network tests of bounded, opt-in KORADASO worker queue."""
import sqlite3

import pytest

from mission_control.koradaso_crawl_fleet import (
    approve_seed, fleet_status, revoke_seed, run_due_once,
)


def test_idle_does_not_crawl(tmp_path):
    state, index = tmp_path / "fleet.db", tmp_path / "index.db"
    assert run_due_once(state, index) == {"status": "idle", "indexed": 0}


def test_only_approved_seed_can_run_and_interval_is_enforced(tmp_path):
    state, index = tmp_path / "fleet.db", tmp_path / "index.db"
    calls = []
    def fake_crawl(url, path, *, max_pages):
        calls.append((url, path, max_pages))
        return {"indexed": 2, "errors": []}
    approve_seed(state, "https://example.org/", now=100)
    assert run_due_once(state, index, now=100, crawl=fake_crawl)["status"] == "success"
    assert calls == [("https://example.org/", index, 5)]
    assert run_due_once(state, index, now=101, crawl=fake_crawl)["status"] == "idle"
    assert run_due_once(state, index, now=86500, crawl=fake_crawl)["status"] == "success"
    assert len(calls) == 2
    with sqlite3.connect(state) as db:
        assert db.execute("SELECT COUNT(*) FROM crawl_runs").fetchone()[0] == 2


def test_failed_crawl_backs_off_no_fabricated_index(tmp_path):
    state, index = tmp_path / "fleet.db", tmp_path / "index.db"
    approve_seed(state, "https://example.org/", now=100)
    def denied(*_args, **_kwargs):
        raise ValueError("blocked")
    assert run_due_once(state, index, now=100, crawl=denied)["status"] == "ValueError"
    assert run_due_once(state, index, now=101, crawl=denied)["status"] == "idle"
    assert fleet_status(state)[0]["last_indexed"] == 0


def test_revoke_disables_future_claims(tmp_path):
    state, index = tmp_path / "fleet.db", tmp_path / "index.db"
    approve_seed(state, "https://example.org/", now=100)
    revoke_seed(state, "https://example.org/")
    assert run_due_once(state, index, now=100, crawl=lambda *_a, **_k: None)["status"] == "idle"


def test_reject_private_targets_bad_interval_and_same_database(tmp_path):
    state = tmp_path / "fleet.db"
    for url in ("http://example.org/", "https://127.0.0.1/", "https://localhost/"):
        with pytest.raises(ValueError):
            approve_seed(state, url)
    for hours in (0, 23, 721):
        with pytest.raises(ValueError):
            approve_seed(state, "https://example.org/", interval_hours=hours)
    with pytest.raises(ValueError, match="separate"):
        run_due_once(state, state)
