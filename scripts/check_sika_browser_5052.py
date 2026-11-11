#!/usr/bin/env python3
"""Read-only local SIKA browser/Store smoke check for existing Flask port 5052.

No provisioning, payment execution, service restart, or data modification.
Run: python scripts/check_sika_browser_5052.py
"""
from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE = "http://127.0.0.1:5052"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(path: str):
    request = Request(BASE + path, headers={"Accept": "text/html,application/json"})
    try:
        with build_opener(NoRedirect).open(request, timeout=5) as response:
            return response.status, response.headers, response.read(300_000)
    except HTTPError as exc:
        return exc.code, exc.headers, exc.read(300_000)


def main() -> int:
    checks = []
    try:
        bank_code, bank_headers, bank_body = fetch("/pay/bank")
        checks.append(("Bank page loads", bank_code == 200))
        checks.append(("Account navigation available", b'href="/pay/bank/me"' in bank_body))
        store_code, _, store_body = fetch("/store")
        checks.append(("OAP Store loads", store_code == 200))
        checks.append(("Store browser choice", b"Open in Browser" in store_body))
        cat_code, _, cat_body = fetch("/oap-store/apps")
        item = None
        if cat_code == 200:
            catalogue = json.loads(cat_body)
            item = next((x for x in catalogue.get("apps", ())
                         if x.get("app_id") == "oap.usa_royalty_bank"), None)
        checks.append(("SIKA appears in Store", item is not None))
        checks.append(("Browser routes point to SIKA", bool(item) and
                       item.get("browser_url") == "/pay/bank" and
                       item.get("browser_account_url") == "/pay/bank/me"))
        checks.append(("Install remains blocked", bool(item) and
                       item.get("install_enabled") is False and
                       item.get("install_url") is None))
        account_code, account_headers, account_body = fetch("/pay/bank/me")
        checks.append(("Private account has auth boundary", account_code in (302, 303, 401, 403)))
        checks.append(("Private account response not cached",
                       "no-store" in account_headers.get("Cache-Control", "").lower()))
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        print(f"UNKNOWN: 5052 unreachable or unexpected response ({type(exc).__name__}).")
        return 2
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {label}")
    passed = sum(ok for _, ok in checks)
    print(f"Local SIKA browser checks: {passed}/{len(checks)}; production readiness NOT assessed.")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
