#!/usr/bin/env python3
"""Promote the exact OAP Core immutable image to the existing Render service.

Fail-closed:
- exact service ID only
- exact immutable image only
- dry-run by default
- never reads/replaces env vars
- never creates a new service
- never performs a Git/source build
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = "https://api.render.com/v1"
SERVICE_ID = "srv-d8gfsv0jo6nc73egdlf0"
SERVICE_NAME = "on-any-postcode"
RELEASE_MANIFEST = "deploy/render-core-release.json"


def _release_image() -> str:
    with open(RELEASE_MANIFEST, encoding="utf-8") as handle:
        manifest = json.load(handle)
    service = manifest["service"]
    if service.get("render_service_id") != SERVICE_ID:
        raise RuntimeError("Release manifest service id mismatch")
    image = manifest["image"]["immutable_ref"]
    if not isinstance(image, str) or "@sha256:" not in image:
        raise RuntimeError("Release manifest immutable image is invalid")
    return image
PUBLIC_URL = "https://on-any-postcode.onrender.com"
HEALTH_PATH = "/healthz"


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
            "User-Agent": "OAP-Core-Image-Promotion/1.0",
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
        "image": _release_image(),
        "deploy_payload": {"imageUrl": _release_image()},
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

    image = _release_image()
    deploy = _request(
        "POST",
        f"/services/{SERVICE_ID}/deploys",
        {"imageUrl": image},
    )
    deploy_id = deploy.get("id")
    if not isinstance(deploy_id, str) or not deploy_id.startswith("dep-"):
        raise RuntimeError("Render deploy receipt missing")

    return {
        "applied": True,
        "dry_run": False,
        "service_id": SERVICE_ID,
        "image": image,
        "deploy_id": deploy_id,
        "environment_replaced": False,
        "new_service_created": False,
        "human_authority_final": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform the exact existing-service image promotion.",
    )
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
