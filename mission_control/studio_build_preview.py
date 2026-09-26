"""Browser-isolated, owner-scoped OAP Studio Build Preview runtime.

This runtime never executes generated backend code on the production server.
It stores bounded HTML/CSS/JS candidate bundles, serves them with a restrictive
CSP, and supports versioned inspect/revise/read-back loops.
"""

from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
import uuid
from typing import Any

from . import workspaces

_MAX_FILE_BYTES = 120_000
_ALLOWED_FILES = ("index.html", "styles.css", "app.js")
_FORBIDDEN_HTML = re.compile(
    r"<\s*(script|iframe|object|embed|form|link|meta)\b|javascript:|https?://",
    re.IGNORECASE,
)
_TITLE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _normalise_files(files: object) -> dict[str, str]:
    if not isinstance(files, dict):
        raise ValueError("build_preview_files_required")
    bundle: dict[str, str] = {}
    for name in _ALLOWED_FILES:
        value = files.get(name, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError("build_preview_file_must_be_text")
        if len(value.encode("utf-8")) > _MAX_FILE_BYTES:
            raise ValueError("build_preview_file_too_large")
        bundle[name] = value
    if not bundle["index.html"].strip():
        raise ValueError("build_preview_index_html_required")
    if _FORBIDDEN_HTML.search(bundle["index.html"]):
        raise ValueError("build_preview_html_contains_forbidden_active_content")
    return bundle


def _history(owner_id: object, preview_id: object) -> list[dict[str, Any]]:
    preview = str(uuid.UUID(str(preview_id)))
    rows = workspaces.list_studio_build_preview_records(owner_id, preview, limit=100)
    if len(rows) >= 100:
        raise RuntimeError("build_preview_history_limit_reached")
    versions: list[dict[str, Any]] = []
    previous = "GENESIS"
    for index, row in enumerate(rows, 1):
        try:
            entry = json.loads(row["body"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("build_preview_history_unreadable") from exc
        if not isinstance(entry, dict):
            raise TypeError("build_preview_history_invalid")
        payload = {key: value for key, value in entry.items() if key != "digest"}
        if (
            entry.get("preview_id") != preview
            or entry.get("version") != index
            or entry.get("previous_hash") != previous
            or entry.get("digest") != _digest(payload)
            or entry.get("production_deploy_authorised") is not False
            or entry.get("server_side_execution_authorised") is not False
        ):
            raise RuntimeError("build_preview_history_tampered_or_forked")
        versions.append(entry)
        previous = str(entry["digest"])
    return versions


def _entry(
    *,
    preview_id: str,
    version: int,
    previous_hash: str,
    files: dict[str, str],
    prompt_summary: str,
) -> dict[str, Any]:
    file_hashes = {
        name: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for name, content in files.items()
    }
    payload = {
        "preview_id": preview_id,
        "version": version,
        "previous_hash": previous_hash,
        "prompt_summary": prompt_summary[:280],
        "files": files,
        "file_hashes": file_hashes,
        "production_deploy_authorised": False,
        "server_side_execution_authorised": False,
        "browser_isolated": True,
        "network_access_allowed": False,
        "forms_allowed": False,
        "human_authority_final": True,
    }
    return {**payload, "digest": _digest(payload)}


def create(
    owner_id: object,
    *,
    files: object,
    prompt: object = "",
    stopped: bool = False,
) -> dict[str, Any]:
    if stopped:
        raise PermissionError("STOP: build preview blocked")
    preview_id = str(uuid.uuid4())
    bundle = _normalise_files(files)
    entry = _entry(
        preview_id=preview_id,
        version=1,
        previous_hash="GENESIS",
        files=bundle,
        prompt_summary=str(prompt or ""),
    )
    body = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    record_id = workspaces.add_studio_build_preview_record_atomic(
        owner_id,
        preview_id=preview_id,
        version=1,
        digest=entry["digest"],
        title=f"OAP-BUILD-PREVIEW:{preview_id}:v1",
        body=body,
    )
    saved = _history(owner_id, preview_id)
    if not saved or saved[-1]["digest"] != entry["digest"]:
        raise RuntimeError("build_preview_create_readback_mismatch")
    return _summary(saved[-1], record_id=record_id, read_back_verified=True)


def revise(
    owner_id: object,
    preview_id: object,
    *,
    files: object,
    prompt: object = "",
    expected_last_hash: str,
    stopped: bool = False,
) -> dict[str, Any]:
    if stopped:
        raise PermissionError("STOP: build preview blocked")
    preview = str(uuid.UUID(str(preview_id)))
    versions = _history(owner_id, preview)
    if not versions:
        raise RuntimeError("build_preview_not_found")
    previous = versions[-1]
    if expected_last_hash != previous["digest"]:
        raise RuntimeError("stale_build_preview_version")
    version = int(previous["version"]) + 1
    bundle = _normalise_files(files)
    entry = _entry(
        preview_id=preview,
        version=version,
        previous_hash=str(previous["digest"]),
        files=bundle,
        prompt_summary=str(prompt or previous.get("prompt_summary") or ""),
    )
    body = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    record_id = workspaces.add_studio_build_preview_record_atomic(
        owner_id,
        preview_id=preview,
        version=version,
        digest=entry["digest"],
        title=f"OAP-BUILD-PREVIEW:{preview}:v{version}",
        body=body,
    )
    saved = _history(owner_id, preview)
    if saved[-1]["digest"] != entry["digest"]:
        raise RuntimeError("build_preview_revision_readback_mismatch")
    return _summary(saved[-1], record_id=record_id, read_back_verified=True)


def latest(owner_id: object, preview_id: object) -> dict[str, Any]:
    versions = _history(owner_id, preview_id)
    if not versions:
        raise RuntimeError("build_preview_not_found")
    return versions[-1]


def inspect(owner_id: object, preview_id: object) -> dict[str, Any]:
    entry = latest(owner_id, preview_id)
    source = str(entry["files"]["index.html"])
    title_match = _TITLE.search(source)
    title = html_lib.unescape(title_match.group(1).strip()) if title_match else ""
    counts = {
        "buttons": len(re.findall(r"<\s*button\b", source, re.IGNORECASE)),
        "links": len(re.findall(r"<\s*a\b", source, re.IGNORECASE)),
        "inputs": len(re.findall(r"<\s*(input|textarea|select)\b", source, re.IGNORECASE)),
        "sections": len(re.findall(r"<\s*(section|main|article)\b", source, re.IGNORECASE)),
    }
    return {
        "preview_id": entry["preview_id"],
        "version": entry["version"],
        "digest": entry["digest"],
        "title": title,
        "counts": counts,
        "file_hashes": entry["file_hashes"],
        "browser_isolated": True,
        "network_access_allowed": False,
        "production_deploy_authorised": False,
        "server_side_execution_authorised": False,
        "inspect_ready": True,
        "fix_loop_ready": True,
        "retest_ready": True,
    }


def render_document(owner_id: object, preview_id: object) -> str:
    entry = latest(owner_id, preview_id)
    files = entry["files"]
    css = str(files.get("styles.css") or "").replace("</style", "<\\/style")
    js = str(files.get("app.js") or "").replace("</script", "<\\/script")
    body = str(files.get("index.html") or "")
    if re.search(r"<\s*html\b", body, re.IGNORECASE):
        injected = (
            "<style>" + css + "</style>"
            + "<script>'use strict';" + js + "</script>"
        )
        match = re.search(r"</\s*body\s*>", body, re.IGNORECASE)
        if match:
            return body[: match.start()] + injected + body[match.start() :]
        return body + injected
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<style>" + css + "</style></head><body>"
        + body
        + "<script>'use strict';" + js + "</script></body></html>"
    )


def _summary(
    entry: dict[str, Any],
    *,
    record_id: str | None = None,
    read_back_verified: bool = False,
) -> dict[str, Any]:
    return {
        "preview_id": entry["preview_id"],
        "version": entry["version"],
        "digest": entry["digest"],
        "record_id": record_id,
        "file_hashes": entry["file_hashes"],
        "read_back_verified": read_back_verified,
        "preview_ready": True,
        "inspect_ready": True,
        "revision_ready": True,
        "retest_ready": True,
        "browser_isolated": True,
        "network_access_allowed": False,
        "production_deploy_authorised": False,
        "server_side_execution_authorised": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    return {
        "component": "OAP Studio Live Build Preview Engine",
        "candidate_files_ready": True,
        "isolated_preview_ready": True,
        "inspect_ready": True,
        "revision_ready": True,
        "retest_ready": True,
        "owner_scoped_versions": True,
        "hash_chain_ready": True,
        "production_deploy_authorised": False,
        "server_side_execution_authorised": False,
        "human_authority_final": True,
    }
