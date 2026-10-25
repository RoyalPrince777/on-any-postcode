#!/usr/bin/env python3
"""Read-only, fail-closed APK identity gate before an OAP Home V2 in-place upgrade.

This never installs, uninstalls, signs, starts or changes an Android app.
Requires authorized copies of the *currently installed original* and candidate APK.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

EXPECTED_PACKAGE = "com.onanypostcode.oaphome"
EXPECTED_LABEL = "OAP Home V2"
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


def verify(original: Path, candidate: Path) -> str:
    original_package, original_code, _, original_certs = inspect_apk(original)
    candidate_package, candidate_code, candidate_version, candidate_certs = inspect_apk(candidate)
    if original_package != EXPECTED_PACKAGE or candidate_package != EXPECTED_PACKAGE:
        raise BlockedUpgrade("Both APKs must identify the one ORIGINAL OAP Home app")
    if original_certs != candidate_certs:
        raise BlockedUpgrade("APK certificates DIFFER: replacement would be unsafe")
    if candidate_code <= original_code:
        raise BlockedUpgrade("Candidate Android versionCode is not higher than installed")
    if not candidate_version.startswith("2."):
        raise BlockedUpgrade("Candidate is not an OAP Home V2 version")
    candidate_badging = command("aapt", "dump", "badging", str(candidate))
    if f"application-label:'{EXPECTED_LABEL}'" not in candidate_badging:
        raise BlockedUpgrade("Candidate Home display name is not OAP Home V2")
    return ("IDENTITY_GATE_PASSED (offline only): original package, one matching "
            "signer, higher versionCode, V2 label. No installation or data migration "
            "has been performed. Device acceptance and Founder Final remain required.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-original-apk", required=True, type=Path)
    parser.add_argument("--candidate-apk", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(verify(args.installed_original_apk, args.candidate_apk))
        return 0
    except BlockedUpgrade as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
