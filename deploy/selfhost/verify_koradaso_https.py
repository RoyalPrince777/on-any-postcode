#!/usr/bin/env python3
"""Read-only, fail-closed KORADASO first-party HTTPS release probe.

Requires two explicit, distinct first-party DNS hostnames. Never provisions
DNS, TLS, VPS, secrets or starts a deployment. No cookies or auth credentials.
"""
from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import re
import socket
import ssl
from urllib.parse import urlsplit


def verified_host(raw: str, *, resolver=socket.getaddrinfo) -> str:
    host = raw.strip().lower()
    if not 4 <= len(host) <= 253 or not re.fullmatch(r"[a-z0-9.-]+", host):
        raise ValueError("invalid_hostname")
    if ".." in host or host.startswith("-") or host.endswith("-") or "." not in host:
        raise ValueError("invalid_hostname")
    if any(not label or label.startswith("-") or label.endswith("-") for label in host.split(".")):
        raise ValueError("invalid_hostname")
    if host == "localhost" or host.endswith((".localhost", ".local", ".onrender.com")):
        raise ValueError("forbidden_hostname")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("ip_literal_forbidden")
    try:
        answers = resolver(host, 443, type=socket.SOCK_STREAM)
        addresses = [ipaddress.ip_address(row[4][0]) for row in answers]
    except (OSError, ValueError) as exc:
        raise ValueError("dns_not_verified") from exc
    if not addresses or any(not ip.is_global for ip in addresses):
        raise ValueError("not_public_dns")
    return host


def _get(host: str, path: str) -> tuple[int, str]:
    client = http.client.HTTPSConnection(
        host, port=443, timeout=8, context=ssl.create_default_context()
    )
    try:
        client.request("GET", path, headers={
            "User-Agent": "OAP-KORADASO-release-gate/1",
            "Accept": "text/html",
            "Connection": "close",
            "Cache-Control": "no-cache",
        })
        response = client.getresponse()
        status = int(response.status)
        location = response.getheader("Location", "")
        response.read(512)
        return status, location
    finally:
        client.close()


def _private_denied(status: int, location: str, host: str) -> bool:
    if status in (401, 403):
        return True
    if status not in (301, 302, 303, 307, 308):
        return False
    if not location:
        return False
    link = urlsplit(location)
    if link.scheme and link.scheme != "https":
        return False
    if link.netloc and link.netloc.lower() != host:
        return False
    return any(term in link.path.lower() for term in ("sign-in", "signin", "login", "/auth/"))


def verify_release(public: str, private: str, *, resolver=socket.getaddrinfo, get=None) -> dict[str, object]:
    """No external requests are attempted until host validation succeeds."""
    try:
        public = verified_host(public, resolver=resolver)
        private = verified_host(private, resolver=resolver)
        if public == private:
            raise ValueError("public_private_hostname_must_differ")
    except ValueError as exc:
        return {"status": "blocked", "reason": str(exc), "release_approved": False}
    fetch = get or _get
    try:
        public_status, _ = fetch(public, "/koradaso")
        private_status, private_redirect = fetch(private, "/mission/smi")
    except (OSError, ssl.SSLError, TimeoutError, http.client.HTTPException) as exc:
        return {"status": "unknown", "reason": type(exc).__name__, "release_approved": False}
    public_ok = public_status == 200
    private_ok = _private_denied(private_status, private_redirect, private)
    return {
        "status": "https_and_anonymous_boundary_passed" if public_ok and private_ok else "blocked",
        "public_status": public_status, "private_status": private_status,
        "public_https_verified": public_ok, "private_anonymous_denied": private_ok,
        "release_approved": False,
        "redmi_device_verified": False,
        "founder_final_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KORADASO public and SMI HTTPS proof")
    parser.add_argument("--public-host", required=True, help="Approved public OAP DNS hostname")
    parser.add_argument("--private-host", required=True, help="Distinct approved private SMI DNS hostname")
    args = parser.parse_args()
    proof = verify_release(args.public_host, args.private_host)
    print(json.dumps(proof, sort_keys=True))
    return 0 if proof["status"] == "https_and_anonymous_boundary_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
