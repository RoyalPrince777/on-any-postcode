#!/usr/bin/env python3
"""Read-only on-device KORADASO acceptance snapshot (Termux / Redmi).

Does not install/update the APK, grant permissions or claim production signing.
Only requests 127.0.0.1:5052; never sends identity, secrets or private data.
"""
from __future__ import annotations

import json
import subprocess
from urllib import error, request


class _NoRedirect(request.HTTPRedirectHandler):
    """Prevent any loopback probe from following a redirect off the device."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _command(*args: str) -> str:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=5, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _local_page() -> int:
    opener = request.build_opener(request.ProxyHandler({}), _NoRedirect())
    req = request.Request(
        "http://127.0.0.1:5052/koradaso",
        headers={"User-Agent": "KORADASO-Redmi-install-proof/1"},
    )
    try:
        with opener.open(req, timeout=5) as response:
            return int(response.status)
    except (error.URLError, OSError, TimeoutError):
        return 0


def inspect_redmi(*, command=None, local_page=None) -> dict[str, object]:
    run = command or _command
    page = local_page or _local_page
    model = run("getprop", "ro.product.model")[:100]
    installed_path = run("pm", "path", "com.onanypostcode.oapworld")
    package_detected = any(
        line.startswith("package:") and line.endswith(".apk")
        for line in installed_path.splitlines()
    )
    try:
        local_status = page()
    except (OSError, ValueError):
        local_status = 0
    return {
        "status": "device_probe_observed" if model and package_detected and local_status == 200 else "unknown",
        "device_model": model or "unknown",
        "android_package_detected": package_detected,
        "public_5052_http_status": local_status,
        "signed_release_identity_verified": False,
        "app_navigation_verified": False,
        "offline_ai_verified": False,
        "production_certified": False,
    }


def main() -> int:
    result = inspect_redmi()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "device_probe_observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
