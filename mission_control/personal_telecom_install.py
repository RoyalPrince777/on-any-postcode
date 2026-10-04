"""Install/readiness orchestration for the personal OAP telecom control plane.

This installer prepares only OAP-owned software state. It never provisions a
carrier profile, transmits RF, allocates a public number, or stores telecom
authentication secrets. External authority references are supplied by the
Founder and treated as opaque evidence references.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from . import personal_telecom

INSTALL_ROOT_ENV = "OAP_PERSONAL_TELECOM_HOME"
DEFAULT_INSTALL_ROOT = "~/.local/share/oap/personal-telecom"

REFERENCE_ENV = {
    "carrier_profile": "OAP_CARRIER_PROFILE_AUTHORITY_REF",
    "carrier_activation": "OAP_CARRIER_ACTIVATION_AUTHORITY_REF",
    "private_radio": "OAP_PRIVATE_RADIO_AUTHORITY_REF",
    "public_number": "OAP_PUBLIC_NUMBER_AUTHORITY_REF",
}

MANIFEST_NAME = "install-state.json"


def _install_root() -> Path:
    raw = os.environ.get(INSTALL_ROOT_ENV, DEFAULT_INSTALL_ROOT)
    return Path(raw).expanduser()


def authority_references() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for track_id, env_name in REFERENCE_ENV.items():
        value = (os.environ.get(env_name) or "").strip()
        result[track_id] = {
            "env_name": env_name,
            "configured": bool(value),
            "reference_exposed": False,
        }
    return result


def preflight() -> dict[str, object]:
    telecom = personal_telecom.status()
    refs = authority_references()
    return {
        "system": "OAP Personal Telecom Installer",
        "software_contract_valid": telecom["validation"]["passed"],
        "single_owner": telecom["validation"]["single_owner"],
        "single_primary_line": telecom["validation"]["single_primary_line"],
        "oap_number": telecom["line"]["oap_number"],
        "authority_references": refs,
        "external_execution_enabled": any(telecom["execution"].values()),
        "sensitive_material_exposed": False,
        "ready_to_install_software": bool(
            telecom["validation"]["passed"]
            and not any(telecom["execution"].values())
        ),
        "external_activation_ready": all(
            item["configured"] for item in refs.values()
        ),
        "human_authority_final": True,
    }


def _manifest() -> dict[str, object]:
    telecom = personal_telecom.status()
    refs = authority_references()
    return {
        "schema": "oap.personal-telecom.install.v1",
        "system": "OAP Personal Telecom",
        "owner_scope": telecom["line"]["owner_scope"],
        "line_name": telecom["line"]["line_name"],
        "oap_number": telecom["line"]["oap_number"],
        "path": telecom["path"],
        "services": telecom["line"]["services"],
        "device_binding": {
            "mode": telecom["line"]["device_binding"]["mode"],
            "binding_status": telecom["line"]["device_binding"]["binding_status"],
        },
        "authority_reference_state": {
            key: bool(value["configured"]) for key, value in refs.items()
        },
        "execution": telecom["execution"],
        "rollback": {
            "preserve_oap_number": True,
            "revoke_old_binding_before_rebind": True,
            "manifest_removal_disables_local_install_state": True,
        },
        "sensitive_material_exposed": False,
        "human_authority_final": True,
    }


def install(*, assume_yes: bool = False, dry_run: bool = True) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")

    check = preflight()
    if not check["ready_to_install_software"]:
        raise RuntimeError("Personal telecom software preflight failed")

    manifest = _manifest()
    root = _install_root()
    manifest_path = root / MANIFEST_NAME

    if not dry_run:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        encoded = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        manifest_path.write_text(encoded, encoding="utf-8")
        manifest_path.chmod(0o600)

    return {
        "system": "OAP Personal Telecom Installer",
        "dry_run": dry_run,
        "installed": not dry_run,
        "install_root": str(root),
        "manifest_name": MANIFEST_NAME,
        "software_ready": True,
        "external_activation_ready": check["external_activation_ready"],
        "authority_reference_state": manifest["authority_reference_state"],
        "external_execution_changed": False,
        "sensitive_material_exposed": False,
        "human_authority_final": True,
    }


def uninstall(*, assume_yes: bool = False, dry_run: bool = True) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")

    root = _install_root()
    manifest_path = root / MANIFEST_NAME
    existed = manifest_path.exists()

    if not dry_run and existed:
        manifest_path.unlink()
        try:
            root.rmdir()
        except OSError:
            pass

    return {
        "system": "OAP Personal Telecom Installer",
        "dry_run": dry_run,
        "removed": bool(existed and not dry_run),
        "oap_number_preserved": True,
        "external_execution_changed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    root = _install_root()
    manifest_path = root / MANIFEST_NAME
    check = preflight()
    return {
        "system": "OAP Personal Telecom Install Readiness",
        "installer_built": True,
        "install_root": str(root),
        "manifest_present": manifest_path.is_file(),
        "software_ready": check["ready_to_install_software"],
        "external_activation_ready": check["external_activation_ready"],
        "authority_references": check["authority_references"],
        "rollback_built": True,
        "external_execution_enabled": False,
        "sensitive_material_exposed": False,
        "human_authority_final": True,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="oap-personal-telecom-install")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()

    if args.status:
        payload = status()
    elif args.uninstall:
        payload = uninstall(assume_yes=args.yes, dry_run=not args.apply)
    else:
        payload = install(assume_yes=args.yes, dry_run=not args.apply)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
