#!/usr/bin/env python3
"""Read-only independent external proof of the published OAP PTT install route.

Run from an external GitHub Actions runner (NOT within the Flask test client).
Success proves public route content, not PWA installation, Android readiness,
deployment revision identity, or two-device WebRTC audio.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

PUBLIC_ORIGIN = "https://on-any-postcode.onrender.com"
TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 300_000


def _fetch(path: str, *, accept: str = "text/html") -> tuple[int, str, str]:
    request = urllib.request.Request(
        PUBLIC_ORIGIN + path,
        headers={
            "Accept": accept,
            "User-Agent": "OAP-PTT-Store-External-Proof/1.0",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError(f"oversized_external_response: {path}")
        if response.url.split("?", 1)[0] != PUBLIC_ORIGIN + path:
            raise ValueError(f"unexpected_redirect: {path}")
        return response.status, response.headers.get("Content-Type", ""), body.decode(
            "utf-8", errors="replace"
        )


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def main() -> int:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        print("PTT_STORE_PUBLIC_PROBE_UNVERIFIED: requires independent GitHub Actions network")
        return 2
    try:
        status, _, _ = _fetch("/healthz", accept="application/json")
        _require(status == 200, "healthz_not_200")

        status, _, html = _fetch("/store")
        _require(status == 200, "store_not_200")
        _require("data-oap-store-ptt-install-help" in html, "new_store_install_guidance_not_deployed")
        _require("href=\"/ptt?source=oap-store&amp;install=1\"" in html,
                 "store_install_route_not_deployed")

        status, _, html = _fetch("/ptt")
        _require(status == 200, "ptt_page_not_200")
        _require("data-oap-ptt-browser-install-help" in html,
                 "ptt_browser_install_guidance_not_deployed")
        _require('href="/ptt/manifest.webmanifest"' in html,
                 "ptt_manifest_link_missing")

        status, content_type, body = _fetch(
            "/ptt/manifest.webmanifest", accept="application/manifest+json"
        )
        _require(status == 200, "manifest_not_200")
        _require("application/manifest+json" in content_type,
                 "manifest_content_type_invalid")
        manifest = json.loads(body)
        _require(manifest.get("id") == "/ptt", "manifest_id_mismatch")
        _require(manifest.get("scope") == "/ptt", "manifest_scope_mismatch")
        _require(manifest.get("display") == "standalone", "manifest_not_standalone")

        status, _, script = _fetch("/assets/oap-os.js", accept="application/javascript")
        _require(status == 200, "install_controller_not_200")
        _require("isAndroidEmbeddedView" in script, "webview_install_guard_not_deployed")
        _require("this alone does not prove it was installed separately" in script,
                 "install_claim_hardening_not_deployed")

    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        # Never promote public launch readiness on inaccessible or stale content.
        print(json.dumps({
            "event": "oap_ptt_live_store_install_proof",
            "verified": False,
            "scope": "public_installer_routes_only",
            "reason": str(exc)[:240],
        }, sort_keys=True))
        return 1

    print(json.dumps({
        "event": "oap_ptt_live_store_install_proof",
        "verified": True,
        "origin": PUBLIC_ORIGIN,
        "scope": "public_installer_routes_only",
        "android_device_installed": False,
        "native_apk_claimed": False,
        "ptt_live_audio_proven": False,
    }, sort_keys=True))
    print("OAP_PTT_LIVE_STORE_INSTALL_ROUTE_PROOF_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
