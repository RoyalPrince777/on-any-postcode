#!/usr/bin/env python3
"""Promote the exact OAP SMI immutable image to the existing Render service."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = "https://api.render.com/v1"
SERVICE_ID = "srv-da6tp615efls73ct81q0"
SERVICE_NAME = "oap-smi"
IMAGE = (
    "ghcr.io/royalprince777/on-any-postcode-runtime@"
    "sha256:e23632e68641d7bdf8bc6f1e23596336537aec4cf101a748b229acddd70d8622"
)
PUBLIC_URL = "https://oap-smi.onrender.com"
HEALTH_PATH = "/healthz"
RUNTIME_TARGET = "smi_gateway:app"


def _token() -> str:
    return (
        os.environ.get("OAP_RENDER_API_KEY", "").strip()
        or os.environ.get("RENDER_API_KEY", "").strip()
    )


def _request(method: str, path: str, payload: dict | None = None) -> dict:
    token = _token()
    if not token:
        raise RuntimeError("Render API key is not configured")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_BASE + path,
        data=body,
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "OAP-SMI-Image-Promotion/1.0",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read(512_000)
    except urllib.error.HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", "replace")
        raise RuntimeError(f"Render API failed with status {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Render API is unavailable") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Render returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Render returned an invalid response")
    return data


def _assert_service(service: dict) -> None:
    if service.get("id") != SERVICE_ID:
        raise RuntimeError("Unexpected Render service id")
    if service.get("name") != SERVICE_NAME:
        raise RuntimeError("Unexpected Render service name")
    details = service.get("serviceDetails")
    if not isinstance(details, dict):
        raise RuntimeError("Render service details missing")
    if details.get("url") != PUBLIC_URL:
        raise RuntimeError("Unexpected Render public URL")
    if details.get("healthCheckPath") != HEALTH_PATH:
        raise RuntimeError("Unexpected Render health path")


def plan() -> dict[str, object]:
    return {
        "service_id": SERVICE_ID,
        "service_name": SERVICE_NAME,
        "public_url": PUBLIC_URL,
        "health_path": HEALTH_PATH,
        "runtime_target": RUNTIME_TARGET,
        "image": IMAGE,
        "update_payload": {"image": {"name": IMAGE}, "autoDeploy": "no"},
        "deploy_payload": {"imageUrl": IMAGE},
        "creates_new_service": False,
        "replaces_environment": False,
        "source_build_required": False,
        "human_authority_final": True,
    }


def promote(*, apply: bool = False) -> dict[str, object]:
    action = plan()
    if not apply:
        return {"applied": False, "dry_run": True, "plan": action}
    current = _request("GET", f"/services/{SERVICE_ID}")
    _assert_service(current)
    updated = _request(
        "PATCH",
        f"/services/{SERVICE_ID}",
        {"image": {"name": IMAGE}, "autoDeploy": "no"},
    )
    _assert_service(updated)
    image_path = updated.get("imagePath")
    if image_path not in (None, IMAGE):
        raise RuntimeError("Render returned an unexpected image path")
    deploy = _request(
        "POST",
        f"/services/{SERVICE_ID}/deploys",
        {"imageUrl": IMAGE},
    )
    deploy_id = deploy.get("id")
    if not isinstance(deploy_id, str) or not deploy_id.startswith("dep-"):
        raise RuntimeError("Render deploy receipt missing")
    return {
        "applied": True,
        "dry_run": False,
        "service_id": SERVICE_ID,
        "image": IMAGE,
        "deploy_id": deploy_id,
        "environment_replaced": False,
        "new_service_created": False,
        "human_authority_final": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = promote(apply=args.apply)
    except RuntimeError as exc:
        print(json.dumps({"success": False, "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({"success": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
