"""Private, read-only adapter to the installed OAP native navigation engine.

No extra server, public proxy, network fallback, or release authority.
Static code is pinned to the previously delivered quality upgrade.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

ASSET_DIR = Path.home() / "ebike-backend-master/web/transport"
PREFIX = "/mission/smi/maps/"
ASSETS = {
    "": ("navigation.html", "text/html", "510d4db8e9a013fed9a1c546b3c638e35246fe1c06b42c7f441bc640539fa8bf"),
    "navigation.mjs": ("navigation.mjs", "text/javascript", "3b669d29b17e746834c21e3995374f8606512dac7b048ad65bd312017bb59ace"),
    "navigation.css": ("navigation.css", "text/css", "b2a8734eed2e68835cdcce0ef2831f83117c17303a3eae5b5e33a0f0e4c049ba"),
}
API_KEYS = {
    "api/navigation/status": set(),
    "api/navigation/search": {"q"},
    "api/navigation/route": {"from", "to", "mode"},
}
MAX_BODY = 4 * 1024 * 1024


def error(status, reason):
    return status, "application/json", json.dumps({"error": reason}).encode()


def private_context(local_mode, host):
    return local_mode and host in {"127.0.0.1:5000", "localhost:5000"}


def asset(path):
    name, mime, digest = ASSETS[path]
    try:
        with (ASSET_DIR / name).open("rb") as handle:
            raw = handle.read(65537)
    except OSError:
        return error(503, "Install the existing OAP Navigation Quality Upgrade")
    if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != digest:
        return error(503, "Navigation asset revision not approved")
    if name == "navigation.html":
        raw = raw.replace(b'href="/navigation.css"', b'href="navigation.css"')
        raw = raw.replace(b'src="/navigation.mjs"', b'src="navigation.mjs"')
    if name == "navigation.mjs":
        raw = raw.replace(b"'/api/navigation/", b"'api/navigation/")
        raw = raw.replace(b"'/roads/", b"'roads/")
    return 200, mime, raw


def upstream_target(path, query):
    if path in API_KEYS:
        required = API_KEYS[path]
    elif path == "roads/manifest.json" or re.fullmatch(r"roads/-?\d{1,9}_-?\d{1,9}\.json", path):
        required = set()
    else:
        raise LookupError("not_allowed")
    if len(query) > 1000:
        raise ValueError("query_too_long")
    pairs = parse_qsl(query.decode("ascii"), keep_blank_values=True,
                      strict_parsing=True, max_num_fields=3, errors="strict")
    if len(pairs) != len(required) or {k for k, _ in pairs} != required:
        raise ValueError("unexpected_parameters")
    if any(len(v) > 256 or any(ord(c) < 32 for c in v) for _, v in pairs):
        raise ValueError("invalid_parameter")
    if path == "api/navigation/route" and dict(pairs)["mode"] not in {"walk", "bike", "car"}:
        raise ValueError("invalid_mode")
    return "/" + path + ("?" + urlencode(pairs) if pairs else "")


def response(path, query):
    if path in ASSETS:
        if query:
            return error(400, "Unexpected asset query")
        return asset(path)
    try:
        target = upstream_target(path, query)
    except LookupError:
        return error(404, "Navigation route not found")
    except (ValueError, UnicodeError):
        return error(400, "Invalid navigation request")
    conn = http.client.HTTPConnection("127.0.0.1", 3001, timeout=12)
    try:
        # No client credentials, cookies, headers or external addresses forwarded.
        conn.request("GET", target, headers={"Accept": "application/json", "Connection": "close"})
        upstream = conn.getresponse()
        if upstream.status not in {200, 400, 404, 422, 429, 503}:
            return error(502, "Unexpected navigation response")
        if upstream.getheader("Content-Type", "").split(";")[0].strip() != "application/json":
            return error(502, "Navigation response is not JSON")
        raw = upstream.read(MAX_BODY + 1)
        if len(raw) > MAX_BODY:
            return error(502, "Navigation response too large")
        payload = json.loads(raw)
        if not isinstance(payload, (dict, list)):
            return error(502, "Invalid navigation response")
        return upstream.status, "application/json", raw
    except (OSError, http.client.HTTPException, ValueError):
        return error(503, "Local navigation engine unavailable")
    finally:
        conn.close()
