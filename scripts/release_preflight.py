#!/usr/bin/env python3
"""OAP release preflight.

Read-only. Produces one truth-mode decision before any Render mutation/build.
It never creates services, triggers deploys, or exposes provider credentials.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_MANIFEST = ROOT / "deploy" / "render-core-release.json"
SMI_REQUEST = ROOT / "deploy" / "requests" / "smi-image-promote.json"


def _has_render_api_credential() -> bool:
    return bool(
        (os.environ.get("OAP_RENDER_API_KEY") or "").strip()
        or (os.environ.get("RENDER_API_KEY") or "").strip()
    )


def _has_render_deploy_hook() -> bool:
    return bool((os.environ.get("RENDER_DEPLOY_HOOK_URL") or "").strip())


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"invalid_json_object:{path.name}")
    return data


def status() -> dict[str, object]:
    core = _read_json(CORE_MANIFEST)
    smi = _read_json(SMI_REQUEST)

    core_ref = str(core.get("image", {}).get("immutable_ref") or "")
    smi_digest = str(smi.get("image_digest") or "")

    errors: list[str] = []
    if not core_ref.startswith("ghcr.io/") or "@sha256:" not in core_ref:
        errors.append("core_immutable_image_missing")
    if not smi_digest.startswith("sha256:"):
        errors.append("smi_immutable_image_missing")

    api_credential = _has_render_api_credential()
    deploy_hook = _has_render_deploy_hook()
    provider_authority = api_credential or deploy_hook
    image_promotion_ready = not errors and provider_authority

    return {
        "component": "OAP Release Control Plane",
        "mode": "truth",
        "read_only_preflight": True,
        "core_release_contract_valid": "core_immutable_image_missing" not in errors,
        "smi_release_contract_valid": "smi_immutable_image_missing" not in errors,
        "render_api_credential_available": api_credential,
        "render_deploy_hook_available": deploy_hook,
        "provider_authority_available": provider_authority,
        "image_promotion_ready": image_promotion_ready,
        "source_build_fallback": "capacity-dependent",
        "recommended_path": (
            "immutable_image_promotion"
            if image_promotion_ready
            else "hold_no_mutation"
        ),
        "blockers": (
            errors
            + ([] if provider_authority else ["render_image_update_authority_missing"])
        ),
        "rules": {
            "same_service_only": True,
            "no_source_rebuild_when_image_exists": True,
            "no_new_service_for_quota_bypass": True,
            "no_fake_green": True,
            "human_authority_final": True,
        },
    }


def main() -> int:
    result = status()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["image_promotion_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
