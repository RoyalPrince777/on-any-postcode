"""Residue-free production health proof for the public Signal path."""

from __future__ import annotations

import json
import time
import uuid

from flask import Flask, jsonify, make_response

from . import postgres_db, public_store

_PROBE_TTL_SECONDS = 30.0
_probe_cache: tuple[float, bool] | None = None


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _roundtrip_probe(*, force: bool = False) -> bool:
    """Prove Signal can write/read production storage and leave no probe residue."""

    global _probe_cache
    now = time.monotonic()
    if not force and _probe_cache and now - _probe_cache[0] < _PROBE_TTL_SECONDS:
        return bool(_probe_cache[1])
    if not postgres_db.configured():
        _probe_cache = (now, False)
        return False

    identity_id = str(uuid.uuid4())
    marker = f"oap-signal-probe-{uuid.uuid4()}"
    payload = json.dumps(
        {"name": "OAP Probe", "body": marker},
        separators=(",", ":"),
    )
    post_id = ""
    ready = False
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO users(id,username,status)
                   VALUES (%s,%s,'active')""",
                (identity_id, f"oap-signal-probe-{identity_id.replace('-', '')}"),
            )
            row = connection.execute(
                """INSERT INTO posts(user_id,body,scope,status)
                   VALUES (%s,%s,%s,'published') RETURNING id""",
                (identity_id, payload, public_store.PUBLIC_SIGNAL_SCOPE),
            ).fetchone()
            post_id = str(row[0]) if row else ""
            observed = connection.execute(
                """SELECT body FROM posts
                   WHERE id=%s AND user_id=%s AND scope=%s AND status='published'""",
                (post_id, identity_id, public_store.PUBLIC_SIGNAL_SCOPE),
            ).fetchone()
            ready = bool(observed and marker in str(observed[0]))
            connection.rollback()

        with postgres_db.connect(readonly=True) as connection:
            residue = connection.execute(
                """SELECT
                     EXISTS(SELECT 1 FROM users WHERE id=%s) OR
                     EXISTS(SELECT 1 FROM posts WHERE id=%s)""",
                (identity_id, post_id),
            ).fetchone()
            ready = bool(ready and residue and not bool(residue[0]))
    except Exception:  # noqa: BLE001 - health proof must fail closed.
        ready = False

    _probe_cache = (now, ready)
    return ready


def register(app: Flask) -> None:
    """Register a public-safe Signal health endpoint and startup proof."""

    startup_ready = _roundtrip_probe(force=True)
    app.logger.info(
        "signal_roundtrip_startup=%s",
        "ready" if startup_ready else "unavailable",
    )

    @app.get("/signal/health")
    def signal_health():
        ready = _roundtrip_probe()
        return _no_store(
            make_response(
                jsonify(status="healthy" if ready else "unavailable"),
                200 if ready else 503,
            )
        )
