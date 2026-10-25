#!/usr/bin/env python3
"""Read-only APK update gate for the existing V2 Android app.

V2 stays com.onanypostcode.oaphome.v2, with the visible label OAP Home.
The older com.onanypostcode.oaphome is a *different* package and must not be
confused with the V2 signing certificate or silently uninstalled here.

This tool never installs, uninstalls, signs, starts or changes any Android app.
Requires trusted copies of the currently installed V2 and candidate V2 APKs.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

EXPECTED_PACKAGE = "com.onanypostcode.oaphome.v2"
LEGACY_PACKAGE = "com.onanypostcode.oaphome"
EXPECTED_LABEL = "OAP Home"
PACKAGE_LINE = re.compile(
    r"^package: name='([^']+)' versionCode='([0-9]+)'(?: versionName='([^']*)')?"
)
CERT_LINE = re.compile(r"^Signer #([0-9]+) certificate SHA-256 digest: ([0-9a-fA-F]{64})$")


class BlockedUpgrade(RuntimeError):
    """Missing or contradictory evidence must never authorize an update."""


def command(binary: str, *args: str) -> str:
    found = shutil.which(binary)
    if not found:
        raise BlockedUpgrade(f"{binary} is unavailable; cannot verify the APK offline")
    try:
        result = subprocess.run(
            [found, *args], check=False, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BlockedUpgrade(f"{binary} inspection could not complete") from exc
    if result.returncode != 0:
        raise BlockedUpgrade(f"{binary} rejected the APK; no update allowed")
    return result.stdout


def inspect_apk(path: Path) -> tuple[str, int, str, tuple[str, ...]]:
    if not path.is_file() or path.stat().st_size < 10000:
        raise BlockedUpgrade("APK missing or too small to trust; no update allowed")
    badging = command("aapt", "dump", "badging", str(path))
    match = next((PACKAGE_LINE.match(line) for line in badging.splitlines()
                  if PACKAGE_LINE.match(line)), None)
    if not match:
        raise BlockedUpgrade("APK package/version identity not available")
    package, code, version = match.group(1), int(match.group(2)), match.group(3) or ""
    verification = command("apksigner", "verify", "--print-certs", "--verbose", str(path))
    certs = tuple(
        (cert.group(1), cert.group(2).lower())
        for line in verification.splitlines()
        if (cert := CERT_LINE.match(line.strip()))
    )
    if len(certs) != 1 or certs[0][0] != "1":
        raise BlockedUpgrade("APK signing certificate not uniquely established")
    return package, code, version, (certs[0][1],)


def verify(installed_v2: Path, candidate: Path) -> str:
    installed_package, installed_code, _, installed_certs = inspect_apk(installed_v2)
    candidate_package, candidate_code, candidate_version, candidate_certs = inspect_apk(candidate)
    if installed_package != EXPECTED_PACKAGE or candidate_package != EXPECTED_PACKAGE:
        raise BlockedUpgrade(
            "Expected the existing V2 package on BOTH APKs; old Home is separate"
        )
    if installed_certs != candidate_certs:
        raise BlockedUpgrade("V2 APK certificates DIFFER: update would be unsafe")
    if candidate_code <= installed_code:
        raise BlockedUpgrade("Candidate Android versionCode is not higher than installed V2")
    if not candidate_version.startswith("2."):
        raise BlockedUpgrade("Candidate is not an OAP Home V2 version")
    candidate_badging = command("aapt", "dump", "badging", str(candidate))
    if f"application-label:'{EXPECTED_LABEL}'" not in candidate_badging:
        raise BlockedUpgrade("Candidate V2 display name must be OAP Home")
    return (
        "V2_UPDATE_IDENTITY_PASSED (offline only): same installed V2 package, "
        "one matching signer, higher versionCode, OAP Home label. "
        "No installation, default Home switch, or old Home removal performed. "
        "Physical device acceptance and Founder Final remain required."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-v2-apk", required=True, type=Path)
    parser.add_argument("--candidate-apk", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(verify(args.installed_v2_apk, args.candidate_apk))
        return 0
    except BlockedUpgrade as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
