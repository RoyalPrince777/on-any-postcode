#!/usr/bin/env python3
"""Read-only Android OAP Home V2 update evidence from the device.

Runs locally on the phone (for example in Termux), without root. It does not
install or uninstall packages, open Settings, request privileges, access user
files, print APK paths, or contact a remote service.

An app omitted by Android package visibility is UNKNOWN, never "not installed".
No candidate can pass until its identity, version, signature and the installed
V2 identity are all independently readable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

V2_PACKAGE = "com.onanypostcode.oaphome.v2"
LEGACY_PACKAGE = "com.onanypostcode.oaphome"
DISPLAY_LABEL = "OAP Home"
_PACKAGE = re.compile(
    r"^package: name='([^']+)' versionCode='([0-9]+)'(?: versionName='([^']*)')?"
)
_CERT = re.compile(r"^Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]{64})$")
_BASE_APK = re.compile(r"^package:(/[^\r\n]+\.apk)$")


def _run(*args: str) -> str | None:
    """Return stdout only on a successful bounded inspection command."""
    if not shutil.which(args[0]):
        return None
    try:
        completed = subprocess.run(
            args, check=False, timeout=20, capture_output=True, text=True,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout if completed.returncode == 0 else None


def _apk_info(apk: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "package": None, "version_code": None,
        "signer_sha256": None, "label": None,
    }
    try:
        if not apk.is_file() or not apk.stat().st_size:
            return result
    except OSError:
        return result
    badging = _run("aapt", "dump", "badging", str(apk))
    if badging is not None:
        line = next((m for value in badging.splitlines()
                     if (m := _PACKAGE.match(value))), None)
        if line is not None:
            result["package"] = line.group(1)
            result["version_code"] = int(line.group(2))
        name = next(
            (value.split("application-label:'", 1)[1].split("'", 1)[0]
             for value in badging.splitlines()
             if value.startswith("application-label:'")), None
        )
        result["label"] = name
    certs = _run("apksigner", "verify", "--print-certs", "--verbose", str(apk))
    if certs is not None:
        matches = [_CERT.match(value.strip()) for value in certs.splitlines()]
        signers = [m.group(1).lower() for m in matches if m]
        if len(signers) == 1:
            result["signer_sha256"] = signers[0]
    return result


def installed_package(package: str) -> dict[str, object]:
    report: dict[str, object] = {
        "package": package,
        "package_visible": False,
        "visibility": "unknown",
        "version_code": None,
        "signer_sha256": None,
    }
    info = _run("pm", "path", package)
    if info is None:
        return report
    paths = [m.group(1) for line in info.splitlines()
             if (m := _BASE_APK.match(line.strip()))]
    if not paths:
        # Termux may lack package-visibility rights. Never assert absence.
        return report
    report["package_visible"] = True
    report["visibility"] = "visible"
    # Paths are intentionally not emitted in the public report.
    for path in paths:
        metadata = _apk_info(Path(path))
        if metadata["package"] == package:
            report["version_code"] = metadata["version_code"]
            report["signer_sha256"] = metadata["signer_sha256"]
            break
    return report


def inspect(candidate: Path | None = None) -> dict[str, object]:
    v2 = installed_package(V2_PACKAGE)
    legacy = installed_package(LEGACY_PACKAGE)
    result: dict[str, object] = {
        "operation": "read_only_oap_home_v2_update_probe",
        "v2_installed": v2,
        "legacy_home": {
            "package": LEGACY_PACKAGE,
            "visibility": legacy["visibility"],
        },
        "candidate": None,
        "candidate_update_verdict": "HOLD_MISSING_EVIDENCE",
        "no_install_or_uninstall": True,
        "founder_final_required": True,
    }
    if candidate is None:
        return result
    checked = _apk_info(candidate)
    result["candidate"] = checked
    # No bypass for unreadable APKs, missing tools, different signing identities
    # or a not-strictly-newer version. No device mutation follows this verdict.
    if checked["package"] != V2_PACKAGE or checked["label"] != DISPLAY_LABEL:
        return result
    if not isinstance(v2["version_code"], int):
        return result
    if not isinstance(checked["version_code"], int):
        return result
    if checked["version_code"] <= v2["version_code"]:
        result["candidate_update_verdict"] = "HOLD_NOT_NEWER"
        return result
    if not v2["signer_sha256"] or not checked["signer_sha256"]:
        return result
    if v2["signer_sha256"] != checked["signer_sha256"]:
        result["candidate_update_verdict"] = "HOLD_SIGNER_MISMATCH"
        return result
    result["candidate_update_verdict"] = "IDENTITY_COMPATIBLE_NOT_INSTALLED"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-apk", type=Path)
    args = parser.parse_args()
    result = inspect(args.candidate_apk)
    print(json.dumps(result, indent=2, sort_keys=True))
    # A read-only probe is always useful. The verdict, not the process exit
    # status, determines whether evidence authorizes proceeding.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
