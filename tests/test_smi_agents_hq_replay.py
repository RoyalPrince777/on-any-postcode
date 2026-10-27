"""Exercise durable nonce uniqueness without mocked storage."""
import sqlite3

from mission_control.smi_agents_hq_replay import (
    initialise_nonce_store,
    sqlite_atomic_replay_guard,
)


def test_nonce_survives_new_connection_and_guard(tmp_path):
    database = str(tmp_path / "nonces.sqlite3")
    initialise_nonce_store(database)
    first = sqlite_atomic_replay_guard(database)
    assert first("NEO-001", "fresh-nonce") is True
    assert first("NEO-001", "fresh-nonce") is False
    second = sqlite_atomic_replay_guard(database)
    assert second("NEO-001", "fresh-nonce") is False
    assert second("NEO-002", "fresh-nonce") is True


def test_missing_schema_fails_closed(tmp_path):
    database = str(tmp_path / "empty.sqlite3")
    sqlite3.connect(database).close()
    guard = sqlite_atomic_replay_guard(database)
    assert guard("NEO-001", "fresh-nonce") is False


def test_replay_store_missing_file_does_not_auto_create(tmp_path):
    database = tmp_path / "nonexistent.sqlite3"
    try:
        sqlite_atomic_replay_guard(str(database))
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing persistence must fail")
    assert not database.exists()


def test_atomic_uniqueness_across_parallel_connections(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    database = str(tmp_path / "parallel.sqlite3")
    initialise_nonce_store(database)
    guard = sqlite_atomic_replay_guard(database)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: guard("NEO-001", "same-nonce"), range(12)))
    assert results.count(True) == 1
    assert results.count(False) == 11
