"""Opt-in, bounded KORADASO crawl queue; never starts from web/server boot.

Only locally approved HTTPS seed URLs may be executed. Each claim runs the
existing robots/SSRF-protected single-host crawler, not a new network client.
This is source foundation, not a production autonomous web index.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from uuid import uuid4

from .koradaso_public_crawler import CrawlDenied, _target, crawl_public_seed

MAX_SEEDS = 21
MIN_INTERVAL_SECONDS = 24 * 3600
MAX_INTERVAL_SECONDS = 30 * 24 * 3600
RETRY_SECONDS = 3600
LEASE_SECONDS = 120


def init_fleet(state: Path) -> None:
    state.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(state, timeout=10) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS crawl_seeds (
            url TEXT PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 1,
            interval_seconds INTEGER NOT NULL, next_due REAL NOT NULL,
            lease_until REAL, lease_token TEXT, last_result TEXT DEFAULT 'pending',
            last_indexed INTEGER NOT NULL DEFAULT 0
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS crawl_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL,
            started REAL NOT NULL, completed REAL NOT NULL,
            outcome TEXT NOT NULL, indexed INTEGER NOT NULL
        )""")


def approve_seed(state: Path, url: str, *, interval_hours: int = 24,
                 now: float | None = None) -> None:
    url, _ = _target(url)
    if not isinstance(interval_hours, int) or not 24 <= interval_hours <= 720:
        raise ValueError("interval_outside_24_to_720_hours")
    init_fleet(state)
    when = time.time() if now is None else float(now)
    with sqlite3.connect(state, timeout=10) as db:
        db.execute("BEGIN IMMEDIATE")
        exists = db.execute("SELECT 1 FROM crawl_seeds WHERE url=?", (url,)).fetchone()
        if not exists and db.execute("SELECT COUNT(*) FROM crawl_seeds").fetchone()[0] >= MAX_SEEDS:
            raise ValueError("approved_seed_limit_reached")
        # Reapproval cannot evade a prior cooldown or running lease.
        db.execute("""INSERT INTO crawl_seeds(url, interval_seconds, next_due)
            VALUES(?,?,?) ON CONFLICT(url) DO UPDATE SET
            enabled=1, interval_seconds=excluded.interval_seconds""",
            (url, interval_hours * 3600, when))


def revoke_seed(state: Path, url: str) -> None:
    url, _ = _target(url)
    init_fleet(state)
    with sqlite3.connect(state, timeout=10) as db:
        db.execute("UPDATE crawl_seeds SET enabled=0 WHERE url=?", (url,))


def run_due_once(state: Path, index: Path, *, now: float | None = None,
                 crawl=None) -> dict[str, object]:
    """Run at most one due approved seed, with a transactional lease.

    Caller must explicitly invoke this worker; no implicit background start.
    """
    if state.resolve() == index.resolve():
        raise ValueError("fleet_state_must_be_separate_from_index")
    init_fleet(state)
    when = time.time() if now is None else float(now)
    token = uuid4().hex
    with sqlite3.connect(state, timeout=10) as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("""SELECT url, interval_seconds FROM crawl_seeds
            WHERE enabled=1 AND next_due<=?
            AND (lease_until IS NULL OR lease_until<?)
            ORDER BY next_due, url LIMIT 1""", (when, when)).fetchone()
        if row is None:
            return {"status": "idle", "indexed": 0}
        url, interval = row
        db.execute("""UPDATE crawl_seeds SET lease_until=?, lease_token=?
            WHERE url=?""", (when + LEASE_SECONDS, token, url))
    indexed = 0
    outcome = "success"
    try:
        result = (crawl or crawl_public_seed)(url, index, max_pages=5)
        indexed = int(result.get("indexed", 0))
        if result.get("errors"):
            outcome = "crawl_errors"
    except (CrawlDenied, OSError, ValueError, sqlite3.Error) as exc:
        outcome = type(exc).__name__
    completed = time.time() if now is None else when
    due = completed + (interval if outcome == "success" else RETRY_SECONDS)
    with sqlite3.connect(state, timeout=10) as db:
        db.execute("BEGIN IMMEDIATE")
        changed = db.execute("""UPDATE crawl_seeds SET next_due=?, lease_until=NULL,
            lease_token=NULL, last_result=?, last_indexed=?
            WHERE url=? AND lease_token=?""",
            (due, outcome, indexed, url, token)).rowcount
        if changed:
            db.execute("""INSERT INTO crawl_runs
                (url, started, completed, outcome, indexed) VALUES (?,?,?,?,?)""",
                (url, when, completed, outcome, indexed))
    return {"status": outcome if changed else "lease_expired",
            "indexed": indexed if changed else 0, "url": url}


def fleet_status(state: Path) -> list[dict[str, object]]:
    if not state.is_file():
        return []
    with sqlite3.connect(f"file:{state}?mode=ro", uri=True, timeout=2) as db:
        return [{"url": url, "enabled": bool(enabled), "next_due": due,
                 "last_result": result, "last_indexed": indexed}
                for url, enabled, due, result, indexed in db.execute(
                    """SELECT url, enabled, next_due, last_result, last_indexed
                    FROM crawl_seeds ORDER BY url""")]
