#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from urllib import error, request

URL = "https://on-any-postcode.onrender.com/arena"
TIMEOUT_SECONDS = 15
REQUIRED_MARKERS = (
    "OAP ARENA",
    "Global Arena",
    "Postcode",
    "Borough / Region",
    "Country",
    "Continent",
    "Competition",
    "Rankings",
    "Teams",
    "Tournaments",
    "Leagues",
    "Spectator",
    "Disputes",
    "payment execution remain disabled",
)


def probe() -> dict[str, object]:
    req = request.Request(
        URL,
        headers={
            "Accept": "text/html",
            "User-Agent": "OAP-Arena-Green-Gate/1.0",
            "Cache-Control": "no-cache",
        },
    )
    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            status = int(response.status)
            body = response.read().decode("utf-8", errors="replace")
    except (TimeoutError, error.URLError, OSError, UnicodeError) as exc:
        return {
            "ok": False,
            "status": 0,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
            "failure_type": "timeout" if isinstance(exc, TimeoutError) else "request_error",
            "missing_markers": list(REQUIRED_MARKERS),
        }

    missing = [marker for marker in REQUIRED_MARKERS if marker not in body]
    return {
        "ok": status == 200 and not missing,
        "status": status,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "failure_type": None if status == 200 and not missing else "invalid_response",
        "missing_markers": missing,
        "body_bytes": len(body.encode("utf-8")),
    }


def main() -> None:
    result = probe()
    receipt = {
        "event": "oap_arena_bounded_external_probe",
        "url": URL,
        "status": int(result.get("status") or 0),
        "elapsed_ms": float(result.get("elapsed_ms") or 0),
        "body_bytes": int(result.get("body_bytes") or 0),
        "required_markers": len(REQUIRED_MARKERS),
        "missing_markers": result.get("missing_markers") or [],
        "arena_public_surface_proven": bool(result.get("ok")),
        "authentication_performed": False,
        "profile_write_performed": False,
        "payment_performed": False,
        "prize_performed": False,
        "tracking_performed": False,
        "failure_type": result.get("failure_type"),
    }
    print(json.dumps(receipt, sort_keys=True))
    if not result.get("ok"):
        raise SystemExit("live Arena probe failed")


if __name__ == "__main__":
    main()
